"""TotalConnectClient() in this file is the primary class of this package.

Instantiate it like this:

usercodes = { 'default': '1234' }
client = TCC.TotalConnectClient(username, password, usercodes)

for location in client.locations:
    ### do stuff with this location
"""

import base64
import json
import logging
import ssl
from ssl import SSLContext
import time
from importlib import resources as impresources
from typing import Any, Callable, Dict
import requests
import urllib3.poolmanager
import urllib3.util
import zeep
import zeep.cache
import zeep.transports
from zeep.exceptions import Fault as ZeepFault
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from oauthlib.oauth2 import LegacyApplicationClient, TokenExpiredError, OAuth2Error
from requests_oauthlib import OAuth2Session
import jwt

from . import cache as cache_folder
from .const import (
    ArmType,
    _ResultCode,
    SOAP_API_ENDPOINT,
    AUTH_CONFIG_ENDPOINT,
    AUTH_TOKEN_ENDPOINT,
    HTTP_API_ENDPOINT_BASE,
    HTTP_API_SESSION_DETAILS_ENDPOINT,
    HTTP_API_LOGOUT,
)
from .exceptions import (
    AuthenticationError,
    BadResultCodeError,
    FailedToBypassZone,
    FeatureNotSupportedError,
    InvalidSessionError,
    RetryableTotalConnectError,
    ServiceUnavailable,
    TotalConnectError,
    UsercodeInvalid,
    UsercodeUnavailable,
)
from .location import TotalConnectLocation
from .user import TotalConnectUser

DEFAULT_USERCODE = "-1"

SCHEMAS_TO_CACHE = {
    "https://schemas.xmlsoap.org/soap/encoding/": "soap-encodings-schemas.xmlsoap.org.txt",
}

LOGGER = logging.getLogger(__name__)


class _SslContextAdapter(requests.adapters.HTTPAdapter):
    """Makes Zeep use our ssl_context."""

    def __init__(self, ssl_context: SSLContext, **kwargs) -> None:
        self.ssl_context = ssl_context
        super().__init__(**kwargs)

    def init_poolmanager(
        self, num_pools: int, maxsize: int, block: bool = False
    ) -> None:
        self.poolmanager = urllib3.poolmanager.PoolManager(
            num_pools=num_pools,
            maxsize=maxsize,
            block=block,
            ssl_context=self.ssl_context,
        )


class TotalConnectClient:
    """Client for Total Connect."""

    TIMEOUT = 60  # seconds until I/O will fail
    MAX_RETRY_ATTEMPTS = 5 # number of times to retry an API call

    def __init__(  # pylint: disable=too-many-arguments
        self,
        username: str,
        password: str,
        usercodes: Dict[str, str] | None = None,
        auto_bypass_battery: bool = False,
        retry_delay: int = 6,  # seconds between retries
    ) -> None:
        """Initialize."""
        self.times = {}
        self.time_start = time.time()
        self.soap_client = None

        self.username: str = username
        self.password: str = password
        self.usercodes = usercodes or {}
        self.auto_bypass_low_battery = auto_bypass_battery
        self.retry_delay = retry_delay

        self.token = None
        self._oauth_session = None
        self._oauth_client = None
        self._invalid_credentials = False
        self._client_id = None
        self._app_id = None
        self._app_version = None
        self._key_pem = None

        self._module_flags: Dict[str, str] = {}
        self._user: TotalConnectUser | None = None
        self._locations: Dict[Any, TotalConnectLocation] = {}
        self._locations_unfetched: Dict[Any, TotalConnectLocation] = {}

        self.authenticate()

        self.times["__init__"] = time.time() - self.time_start

    @property
    def locations(self) -> Dict[Any, TotalConnectLocation]:
        """Raises an exception if the panel cannot be reached to retrieve
        metadata or details. This can be retried later and will succeed
        if/when the panel becomes reachable.
        """
        # to_fetch is needed because items() is invalidated by del
        to_fetch = list(self._locations_unfetched.items())
        for locationid, location in to_fetch:
            try:
                location.get_partition_details()
                location.get_zone_details()
                location.get_panel_meta_data()
                # if we get here, it has been fetched successfully
                del self._locations_unfetched[locationid]
            except Exception:
                LOGGER.error(f"exception during initial fetch of {locationid}")
                raise
        assert not self._locations_unfetched
        return self._locations

    def __str__(self) -> str:
        """Return a text string that is printable."""
        data = (
            f"CLIENT\n\n"
            f"Username: {self.username}\n"
            f"Password: {'[hidden]' if self.password else '[unset]'}\n"
            f"Usercode: {self.usercodes}\n"
            f"Auto Bypass Low Battery: {self.auto_bypass_low_battery}\n"
            f"Invalid Credentials: {self._invalid_credentials}\n"
            f"Module Flags:\n"
        )

        for key, value in self._module_flags.items():
            data = data + f"  {key}: {value}\n"

        data = data + str(self._user)

        locations = f"LOCATIONS: {len(self.locations)}\n\n"
        for location in self.locations:
            locations = locations + str(self.locations[location])

        return data + locations

    def times_as_string(self) -> str:
        """Return a string with times."""
        self.times["total running time"] = time.time() - self.time_start
        msg = "total-connect-client time info (seconds):\n"
        for key, value in self.times.items():
            msg = msg + f"  {key}: {value}\n"

        return msg

    def _raise_for_retry(self, response: Dict[str, Any]) -> None:
        """Determine which responses should be retried in request()."""
        rc = _ResultCode.from_response(response)
        if rc == _ResultCode.INVALID_SESSION:
            raise InvalidSessionError("invalid session", response)
        if rc == _ResultCode.INVALID_SESSIONID:
            raise InvalidSessionError("invalid session ID", response)
        if rc == _ResultCode.CONNECTION_ERROR:
            raise RetryableTotalConnectError("connection error", response)
        if rc == _ResultCode.FAILED_TO_CONNECT:
            raise RetryableTotalConnectError("failed to connect with panel", response)
        if rc == _ResultCode.BAD_OBJECT_REFERENCE:
            raise RetryableTotalConnectError("bad object reference", response)

    def raise_for_resultcode(self, response: Dict[str, Any]) -> None:
        """If response.ResultCode indicates success, return and do nothing.

        If it indicates an authentication error, raise AuthenticationError.
        """
        rc = _ResultCode.from_response(response)
        if rc in (
            _ResultCode.SUCCESS,
            _ResultCode.ARM_SUCCESS,
            _ResultCode.DISARM_SUCCESS,
            _ResultCode.SESSION_INITIATED,
        ):
            return
        self._raise_for_retry(response)
        if rc in (
            _ResultCode.BAD_USER_OR_PASSWORD,
            _ResultCode.AUTHENTICATION_FAILED,
            _ResultCode.ACCOUNT_LOCKED,
        ):
            raise AuthenticationError(rc.name, response)
        if rc == _ResultCode.USER_CODE_UNAVAILABLE:
            raise UsercodeUnavailable(rc.name, response)
        if rc == _ResultCode.USER_CODE_INVALID:
            raise UsercodeInvalid(rc.name, response)
        if rc == _ResultCode.FEATURE_NOT_SUPPORTED:
            raise FeatureNotSupportedError(rc.name, response)
        if rc == _ResultCode.FAILED_TO_BYPASS_ZONE:
            raise FailedToBypassZone(rc.name, response)
        raise BadResultCodeError(rc.name, response)

    API_ENDPOINT = SOAP_API_ENDPOINT

    def _request_with_retries(
        self,
        do_request: Callable[[], Dict[str, Any]],
        request_description: str,
        attempts_remaining: int = MAX_RETRY_ATTEMPTS,
    ):
        """Call a given request function and handle retries for temporary errors and authentication
        problems."""
        is_first_request = attempts_remaining == self.MAX_RETRY_ATTEMPTS
        attempts_remaining -= 1

        try:
            LOGGER.debug(f"sending API request {request_description}")
            response = do_request()
            self._raise_for_retry(response)
            return response
        # To retry an exception that could be raised during the
        # request, add it to an except block here, depending on what
        # you want to have happen. The first block just retries and
        # logs. The second block causes reauthentication.
        except RetryableTotalConnectError as err:
            if attempts_remaining <= 0:
                raise
            msg = (
                f"{self.username} {request_description} {err.args[0]} on response"
            )
            if is_first_request:
                LOGGER.info(f"{msg}: {attempts_remaining} retries remaining")
            else:
                LOGGER.debug(f"{msg}: {attempts_remaining} retries remaining")
            time.sleep(self.retry_delay)
        except (ZeepFault, requests.RequestException) as err:
            if attempts_remaining <= 0:
                raise ServiceUnavailable(
                    f"Error connecting to Total Connect service: {err}"
                ) from err
            LOGGER.debug(
                f"Error connecting to Total Connect service: {attempts_remaining} retries remaining"
            )
            time.sleep(self.retry_delay)
        except (OAuth2Error, InvalidSessionError) as err:
            if attempts_remaining <= 0:
                raise ServiceUnavailable(
                    f"Invalid Session after multiple retries: {err}"
                ) from err
            LOGGER.info(
                f"reauthenticating {self.username}: {attempts_remaining} retries remaining"
            )
            self.authenticate()

        return self._request_with_retries(do_request, request_description, attempts_remaining)


    def request(
        self,
        operation_name: str,
        args: list[Any] | tuple[Any, ...]
    ) -> Dict[str, Any]:
        """Send a SOAP request.

        args is a list or tuple defining the parameters to the operation.
        """
        if not self.soap_client:
            # the server doesn't support RFC 5746 secure renegotiation, which
            # causes OpenSSL to fail by default. here we override the default.
            # if they fix their server, we should revert this change to ctx.options
            session = requests.Session()
            ctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            ctx.options |= 0x04  # ssl.OP_LEGACY_SERVER_CONNECT once that exists
            session.mount("https://", _SslContextAdapter(ctx))
            cache = zeep.cache.InMemoryCache()
            for url, filename in SCHEMAS_TO_CACHE.items():
                cache_file = impresources.files(cache_folder) / filename
                with cache_file.open() as file:
                    cache.add(url, file.read())
            transport = zeep.transports.Transport(
                session=session,
                cache=cache,
                timeout=self.TIMEOUT,  # for loading WSDL and xsd documents
                operation_timeout=self.TIMEOUT,  # for operations (POST/GET)
            )
            self.soap_client = zeep.Client(SOAP_API_ENDPOINT, transport=transport)

        def _do_soap_request() -> Dict[str, Any]:
            # Refresh session if needed. If the refresh fails it will throw an InvalidSessionError,
            # forcing a reauthentication. This is a mildly hacky way of checking if we need a
            # refresh, the 'add_token' function is generally used to prepare an actual request for
            # sending. But if we call it directly then it has the useful side-effect of throwing an
            # exception if our current token is expired.
            try:
                self._oauth_client.add_token(HTTP_API_ENDPOINT_BASE)
            except TokenExpiredError:
                LOGGER.debug("Session has expired, refreshing now")
                self._oauth_session.refresh_token(AUTH_TOKEN_ENDPOINT)

            # The first argument is always the session token, keep it up to date in case
            # it changes.
            operation_proxy = self.soap_client.service[operation_name]
            return zeep.helpers.serialize_object(operation_proxy(self.token, *args[1:]))

        return self._request_with_retries(_do_soap_request, f"{operation_name}{args}")

    def http_request(
        self,
        endpoint: str,
        method: str,
        params: Dict[str, Any] | None = None,
        data: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Send an HTTP request to a Web API endpoint

        method is the HTTP method, e.g. 'GET', 'POST', 'PUT', 'DELETE'
        params is a dictionary defining the query parameters to add to the endpoint URL
        data is a dictionary defining the query parameter to encode in the request body
        """
        def _do_http_request() -> Dict[str, Any]:
            response = self._oauth_session.request(
                method=method,
                url=endpoint,
                params=params,
                data=data
            )
            if not response.ok:
                LOGGER.debug(
                    f"Received HTTP error code {response.status_code} with response:",
                    response.content
                )
            return response.json()

        args = {**(params or {}), **(data or {})}
        return self._request_with_retries(_do_http_request, f"{method} {endpoint} ({args})")

    def _encrypt_credential(self, credential: str) -> str:
        # Load the key from the PEM file
        key = RSA.importKey(self._key_pem)

        # Create a cipher object using PKCS1_OAEP padding
        cipher = PKCS1_v1_5.new(key)

        # Encrypt the message
        encrypted_message = cipher.encrypt(credential.encode())

        # Encode the encrypted message in base64 for safe transmission
        return base64.b64encode(encrypted_message).decode()

    def authenticate(self) -> None:
        """Login to the system.

        Upon success, self.token is a valid credential
        for further API calls, and self._user and self.locations are valid.
        self.locations will not be refreshed if it was non-empty on entry.
        """
        start_time = time.time()
        if self._invalid_credentials:
            raise AuthenticationError(
                f"not authenticating: password already failed for user {self.username}"
            )

        self._get_configuration()
        self._request_token()

        # Retrieve user and location information.
        if not self._locations:
            response = self.http_request(
                endpoint=HTTP_API_SESSION_DETAILS_ENDPOINT,
                method="GET",
                params={"appId": self._app_id, "appVersion": self._app_version}
            )["SessionDetailsResult"]
            self._module_flags = dict(
                x.split("=") for x in response["ModuleFlags"].split(",")
            )
            self._user = TotalConnectUser(response["UserInfo"])
            self._locations_unfetched = self._make_locations(response)
            self._locations = self._locations_unfetched.copy()
            if not self._locations:
                raise TotalConnectError("no locations found", response)
        LOGGER.info(f"{self.username} authenticated: {len(self._locations)} locations")
        self.times["authenticate()"] = time.time() - start_time

    def _get_configuration(self) -> None:
        """Retrieve application configuration for TotalConnect REST API."""
        response = requests.get(AUTH_CONFIG_ENDPOINT, timeout=self.TIMEOUT)
        if not response.ok:
            raise ServiceUnavailable(
                f"Service configuration is not available at {AUTH_CONFIG_ENDPOINT}"
            )
        config = response.json()
        key = config["AppConfig"][0]["tc2APIKey"]
        self._client_id = config["AppConfig"][0]["tc2ClientId"]
        self._app_id = next(
            info for info in config["brandInfo"] if info["BrandName"] == "totalconnect"
        )["AppID"]
        self._app_version = config["RevisionNumber"] + "." + config["version"].split(".")[-1]
        self._key_pem = '-----BEGIN PUBLIC KEY-----\n' + key + '\n-----END PUBLIC KEY-----'

    def _request_token(self) -> None:
        """Request a JSON Web Token (JWT)."""
        # Encrypt username and password and log in to get a JWT with a session ID.
        self._oauth_client = LegacyApplicationClient(client_id=self._client_id)
        self._oauth_session = OAuth2Session(
            client=self._oauth_client,
            auto_refresh_url=AUTH_TOKEN_ENDPOINT,
            auto_refresh_kwargs={"client_id": self._client_id}
        )
        try:
            self._oauth_session.fetch_token(
                token_url=AUTH_TOKEN_ENDPOINT,
                username=self._encrypt_credential(self.username),
                password=self._encrypt_credential(self.password),
                client_id=self._client_id
            )
        except OAuth2Error as exc:
            try:
                self.raise_for_resultcode(json.loads(exc.json))
            except AuthenticationError:
                self._invalid_credentials = True
                self.token = None
                raise
        jwt_token = jwt.decode(
            self._oauth_session.access_token,
            algorithms="HS256",
            options={"verify_signature": False}
        )
        self.token = jwt_token["ids"].split(';', 1)[0]

    def validate_usercode(self, device_id: str, usercode: str) -> bool:
        """Return True if the usercode is valid for the device."""
        response = self.request(
            "ValidateUserCodeEx",
            ({"SessionId": self.token, "DeviceId": device_id, "UserCode": usercode}, )
        )
        try:
            self.raise_for_resultcode(response)
        except UsercodeInvalid:
            LOGGER.warning(f"usercode {usercode} invalid for device {device_id}")
            return False
        except UsercodeUnavailable:
            LOGGER.warning(f"usercode {usercode} unavailable for device {device_id}")
            return False
        return True

    def is_logged_in(self) -> bool:
        """Return true if the client is logged in to Total Connect."""
        return self.token is not None

    def log_out(self) -> None:
        """Upon return, we are logged out.

        Raises TotalConnectError if we still might be logged in.
        """
        if self.is_logged_in():
            response = self.http_request(
                endpoint=HTTP_API_LOGOUT,
                method="POST",
                params=None
            )            
            self.raise_for_resultcode(response)
            if response["ResultCode"] != 0:
                raise TotalConnectError(f"Logout failed with response code {response['ResultCode']}: {response['ResultData']}")
            LOGGER.info("Logout Successful")
            self.token = None

    def get_number_locations(self) -> int:
        """Return the number of locations.

        Home Assistant needs a way to force the locations to load
        inside a callable function.
        """
        return len(self.locations)

    def _make_locations(
        self, response: Dict[str, Any]
    ) -> Dict[Any, TotalConnectLocation]:
        """Return a dict mapping LocationID to TotalConnectLocation."""
        start_time = time.time()
        new_locations = {}

        for locationinfo in response.get("Locations") or []:
            location_id = locationinfo["LocationID"]
            location = TotalConnectLocation(locationinfo, self)
            new_locations[location_id] = location

            location.auto_bypass_low_battery = self.auto_bypass_low_battery

            # set the usercode for the location
            usercode = (
                self.usercodes.get(location_id)  # noqa: W504
                or self.usercodes.get(str(location_id))
                or self.usercodes.get("default")
            )
            if usercode:
                location.usercode = usercode
            else:
                LOGGER.warning(f"no usercode for location {location_id}")
                location.usercode = DEFAULT_USERCODE

        self.times["_make_locations()"] = time.time() - start_time
        return new_locations


class ArmingHelper:
    """
    For a partition or location, you can call its arm() or disarm() method directly.

    Example: partition.arm(ArmType.AWAY)

    Alternatively, you can use ArmingHelper.
       Example: ArmingHelper(partition).arm_away()
    """

    def __init__(self, partition_or_location) -> None:
        """Initialize ArmingHelper."""
        self.armable = partition_or_location

    def arm_away(self, usercode: str = "") -> None:
        """Arm the system (Away)."""
        self.armable.arm(arm_type=ArmType.AWAY, usercode=usercode)

    def arm_stay(self, usercode: str = "") -> None:
        """Arm the system (Stay)."""
        self.armable.arm(arm_type=ArmType.STAY, usercode=usercode)

    def arm_stay_instant(self, usercode: str = "") -> None:
        """Arm the system (Stay - Instant)."""
        self.armable.arm(arm_type=ArmType.STAY_INSTANT, usercode=usercode)

    def arm_away_instant(self, usercode: str = "") -> None:
        """Arm the system (Away - Instant)."""
        self.armable.arm(arm_type=ArmType.AWAY_INSTANT, usercode=usercode)

    def arm_stay_night(self, usercode: str = "") -> None:
        """Arm the system (Stay - Night)."""
        self.armable.arm(arm_type=ArmType.STAY_NIGHT, usercode=usercode)

    def disarm(self, usercode: str = "") -> None:
        """Disarm the system."""
        self.armable.disarm(usercode=usercode)
