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
import time
from typing import Any, Callable, Dict

import requests
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from oauthlib.oauth2 import LegacyApplicationClient, OAuth2Error
import requests.adapters
from requests_oauthlib import OAuth2Session

from .const import (
    AUTH_CONFIG_ENDPOINT,
    AUTH_TOKEN_ENDPOINT,
    HTTP_API_LOGOUT,
    HTTP_API_SESSION_DETAILS_ENDPOINT,
    ArmType,
    _ResultCode,
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

LOGGER = logging.getLogger(__name__)


class TotalConnectClient:
    """Client for Total Connect."""

    TIMEOUT = 60  # seconds until I/O will fail
    MAX_RETRY_ATTEMPTS = 5  # number of times to retry an API call
    RETRY_ON_HTTP_STATUS_CODES = set([429, 500, 502, 503, 504]) # HTTP status codes indicating server issue

    def __init__(  # pylint: disable=too-many-arguments
        self,
        username: str,
        password: str,
        usercodes: Dict[str, str] | None = None,
        auto_bypass_battery: bool = False,
        retry_delay: int = 6,  # seconds between retries
        load_details: bool = True,
    ) -> None:
        """Initialize."""
        self.times = {}
        self.time_start = time.time()

        self.username: str = username
        self.password: str = password
        self.usercodes = usercodes or {}
        self.auto_bypass_low_battery = auto_bypass_battery
        self.retry_delay = retry_delay

        self._logged_in = False
        self._oauth_session: OAuth2Session | None = None
        self._oauth_client: LegacyApplicationClient | None = None
        self._invalid_credentials = False
        self._client_id = None
        self._app_id = None
        self._app_version = None
        self._key_pem = None

        self._raw_http_session = requests.Session()
        self._raw_http_session.mount(
            "https://",
            requests.adapters.HTTPAdapter(
                max_retries=requests.adapters.Retry(
                    total=self.MAX_RETRY_ATTEMPTS,
                    status_forcelist=self.RETRY_ON_HTTP_STATUS_CODES
                )
            )
        )

        self._module_flags: Dict[str, str] = {}
        self._user: TotalConnectUser | None = None
        self._locations: Dict[int, TotalConnectLocation] = {}
        self._location_details: Dict[int, bool] = {}

        self.authenticate()
        self._get_session_details()

        if load_details:
            self.load_details()

        self.times["__init__"] = time.time() - self.time_start

    @property
    def locations(self) -> Dict[int, TotalConnectLocation]:
        """Public access for locations."""
        return self._locations

    def __str__(self) -> str:  # pragma: no cover
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
        if rc in (_ResultCode.FAILED_TO_CONNECT, _ResultCode.CANNOT_CONNECT):
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
            msg = f"{self.username} {request_description} {err.args[0]} on response"
            if is_first_request:
                LOGGER.info(f"{msg}: {attempts_remaining} retries remaining")
            else:
                LOGGER.debug(f"{msg}: {attempts_remaining} retries remaining")
            time.sleep(self.retry_delay)
        except requests.RequestException as err:
            if attempts_remaining <= 0:
                raise ServiceUnavailable(
                    f"Error connecting to Total Connect service: {err}"
                ) from err
            LOGGER.debug(
                f"Error connecting to Total Connect service: {attempts_remaining} retries remaining"
            )
            time.sleep(self.retry_delay)
        except (OAuth2Error, InvalidSessionError, ValueError) as err:
            LOGGER.debug(f"Invalid session during request.  Attempts remaining: {attempts_remaining}. Error: {err}")
            if attempts_remaining <= 0:
                raise ServiceUnavailable(
                    f"Invalid Session after multiple retries: {err}"
                ) from err
            LOGGER.info(
                f"re-authenticating: {attempts_remaining} retries remaining"
            )
            self.authenticate()

        return self._request_with_retries(
            do_request, request_description, attempts_remaining
        )

    def http_request(
        self,
        endpoint: str,
        method: str,
        params: Dict[str, Any] | None = None,
        data: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        """Send an HTTP request to a Web API endpoint

        method is the HTTP method, e.g. 'GET', 'POST', 'PUT', 'DELETE'
        params is a dictionary defining the query parameters to add to the endpoint URL (usually with GET)
        data is a dictionary defining the query parameter to encode in the request body (usually with POST/PUT)
        """
        LOGGER.debug(
            f"\n----- http_request -----\n\tendpoint: {endpoint}\n\tmethod: {method}\n\tparams: {params}\n\tdata: {data}\n----- end request -----"
        )

        def _do_http_request() -> Dict[str, Any]:
            response = self._oauth_session.request(
                method=method, url=endpoint, params=params, data=data
            )
            LOGGER.debug(
                f"\n----- http response -----\n\tok: {response.ok}\n\tstatus code: {response.status_code}\n\tJSON: {response.json()}\n----- end response -----"
            )
            if not response.ok:
                LOGGER.debug(
                    f"Received HTTP error code {response.status_code} with response:",
                    response.content,
                )
                # If we get a status code indicating that the server has a problem, force a retry
                if response.status_code == 401:
                    raise InvalidSessionError("Received status code 401 during a request. Requesting new token")
                if response.status_code in self.RETRY_ON_HTTP_STATUS_CODES:
                    raise RetryableTotalConnectError(f"Server temporarily unavailable. Status code: {response.status_code}")
            return response.json()

        args = {**(params or {}), **(data or {})}
        return self._request_with_retries(
            _do_http_request, f"{method} {endpoint} ({args})"
        )

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

        Upon success, self._logged_in is True,
        and self._user and self.locations are valid.
        self.locations will not be refreshed if it was non-empty on entry.
        """
        start_time = time.time()
        if self._invalid_credentials:
            raise AuthenticationError(
                f"not authenticating: password already failed for user {self.username}"
            )

        self._get_configuration()
        self._request_token()

        LOGGER.info(f"{self.username} authenticated")
        self.times["authenticate"] = time.time() - start_time

    def _get_configuration(self) -> None:
        """Retrieve application configuration for TotalConnect REST API."""
        response = self._raw_http_session.get(AUTH_CONFIG_ENDPOINT, timeout=self.TIMEOUT)
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
        self._app_version = (
            config["RevisionNumber"] + "." + config["version"].split(".")[-1]
        )
        self._key_pem = (
            "-----BEGIN PUBLIC KEY-----\n" + key + "\n-----END PUBLIC KEY-----"
        )

    def _request_token(self) -> None:
        """Request a token using OAuth2."""

        def token_updater(token):
            """Update the token on auto-refresh.

            Called following successful token auto-refresh by OAuth2Session.
            """
            self._logged_in = True
            LOGGER.debug("Session token was auto-refreshed")

        self._oauth_client = LegacyApplicationClient(client_id=self._client_id)
        self._oauth_session = OAuth2Session(
            client_id=self._client_id,
            client=self._oauth_client,
            auto_refresh_url=AUTH_TOKEN_ENDPOINT,
            auto_refresh_kwargs={"client_id": self._client_id},
            token_updater=token_updater,
        )
        try:
            self._oauth_session.fetch_token(
                token_url=AUTH_TOKEN_ENDPOINT,
                username=self._encrypt_credential(self.username),
                password=self._encrypt_credential(self.password),
                client_id=self._client_id,
            )
        except OAuth2Error as exc:
            try:
                self.raise_for_resultcode(json.loads(exc.json))
            except AuthenticationError:
                self._invalid_credentials = True
                self._logged_in = False
                raise
        self._logged_in = True

    def _get_session_details(self) -> None:
        """Load session and location details.  This could take a long time."""
        response = self.http_request(
            endpoint=HTTP_API_SESSION_DETAILS_ENDPOINT,
            method="GET",
            params={"appId": self._app_id, "appVersion": self._app_version},
        )["SessionDetailsResult"]

        self._module_flags = dict(
            x.split("=") for x in response["ModuleFlags"].split(",")
        )
        self._user = TotalConnectUser(response["UserInfo"])

        self._make_locations(response)
        if not self._locations:
            raise TotalConnectError("no locations found", response)

    def load_details(self, retries=5):
        """Load details for all locations."""
        retry = False
        for location_id, location in self._locations.items():
            if not self._location_details[location_id]:
                try:
                    location.get_partition_details()
                    location.get_zone_details()
                    location.get_panel_meta_data()
                    self._location_details[location_id] = True
                except Exception:
                    LOGGER.debug(
                        f"exception during initial fetch of {location_id}: retries remaining {retries}"
                    )
                    retry = True

        if retry:
            if retries > 0:
                self.load_details(retries - 1)
            else:
                LOGGER.warning("Could not load details for all locations.")

    def is_logged_in(self) -> bool:
        """Return true if the client is logged in to Total Connect."""
        return self._logged_in

    def log_out(self) -> None:
        """Upon return, we are logged out.

        Raises TotalConnectError if we still might be logged in.
        """
        if self.is_logged_in():
            response = self.http_request(endpoint=HTTP_API_LOGOUT, method="POST")
            self.raise_for_resultcode(response)
            if response["ResultCode"] != 0:
                raise TotalConnectError(
                    f"Logout failed with response code {response['ResultCode']}: {response['ResultData']}"
                )
            LOGGER.info("Logout Successful")
            self._logged_in = False

    def get_number_locations(self) -> int:
        """Return the number of locations.

        Home Assistant needs a way to force the locations to load
        inside a callable function.
        """
        return len(self.locations)

    def _make_locations(
        self, response: Dict[str, Any]
    ) -> None:
        """Create dict mapping LocationID to TotalConnectLocation."""
        for locationinfo in response.get("Locations") or []:
            location_id = locationinfo["LocationID"]
            location = TotalConnectLocation(locationinfo, self)

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
                LOGGER.debug(f"no usercode for location {location_id}")
                location.usercode = DEFAULT_USERCODE

            self._locations[location_id] = location
            self._location_details[location_id] = False


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
