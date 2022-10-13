"""TotalConnectClient() in this file is the primary class of this package.
Instantiate it like this:

usercodes = { 'default': '1234' }
client = TCC.TotalConnectClient(username, password, usercodes)

for location in client.locations:
    ### do stuff with this location
"""

import logging
import time

import zeep
import zeep.cache
from zeep.exceptions import Fault as ZeepFault
import zeep.transports
import requests.exceptions

from .const import ArmType, _ResultCode
from .exceptions import (
    AuthenticationError,
    BadResultCodeError,
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

    TIMEOUT = 60  # seconds until SOAP I/O will fail

    def __init__(         # pylint: disable=too-many-arguments
        self,
        username,
        password,
        usercodes=None,
        auto_bypass_battery=False,
        retry_delay=6,  # seconds between retries
    ):
        """Initialize."""
        self.times = {}
        self.time_start = time.time()
        self.soap_client = None

        self.username = username
        self.password = password
        self.usercodes = usercodes or {}
        self.auto_bypass_low_battery = auto_bypass_battery
        self.retry_delay = retry_delay

        self.token = None
        self._invalid_credentials = False
        self._module_flags = None
        self._user = None
        self._locations = {}
        self._locations_unfetched = {}

        self.authenticate()

        self.times["__init__"] = time.time() - self.time_start

    @property
    def locations(self):
        """Raises an exception if the panel cannot be reached to retrieve
        metadata or details. This can be retried later and will succeed
        if/when the panel becomes reachable.
        """
        # to_fetch is needed because items() is invalidated by del
        to_fetch = list(self._locations_unfetched.items())
        for (locationid, location) in to_fetch:
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

    def __str__(self):
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

    def times_as_string(self):
        """Return a string with times."""
        self.times["total running time"] = time.time() - self.time_start
        msg = "total-connect-client time info (seconds):\n"
        for key, value in self.times.items():
            msg = msg + f"  {key}: {value}\n"

        return msg

    def _raise_for_retry(self, response):
        """Used internally to determine which responses should be retried in
        request().
        """
        rc = _ResultCode.from_response(response)
        if rc == _ResultCode.INVALID_SESSION:
            raise InvalidSessionError("invalid session", response)
        if rc == _ResultCode.INVALID_SESSIONID:
            raise InvalidSessionError("invalid session ID", response)
        if rc == _ResultCode.CONNECTION_ERROR:
            raise RetryableTotalConnectError("connection error", response)
        if rc == _ResultCode.FAILED_TO_CONNECT:
            raise RetryableTotalConnectError("failed to connect with panel", response)
        if rc == _ResultCode.AUTHENTICATION_FAILED:
            raise RetryableTotalConnectError("temporary authentication failure", response)
        if rc == _ResultCode.BAD_OBJECT_REFERENCE:
            raise RetryableTotalConnectError("bad object reference", response)


    def raise_for_resultcode(self, response):
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
        if rc == _ResultCode.BAD_USER_OR_PASSWORD:
            raise AuthenticationError(rc.name, response)
        if rc == _ResultCode.USER_CODE_UNAVAILABLE:
            raise UsercodeUnavailable(rc.name, response)
        if rc == _ResultCode.USER_CODE_INVALID:
            raise UsercodeInvalid(rc.name, response)
        if rc == _ResultCode.FEATURE_NOT_SUPPORTED:
            raise FeatureNotSupportedError(rc.name, response)
        raise BadResultCodeError(rc.name, response)

    def _send_one_request(self, operation_name, args):
        LOGGER.debug(f"sending API request {operation_name}{args}")
        operation_proxy = self.soap_client.service[operation_name]
        return zeep.helpers.serialize_object(operation_proxy(*args))

    API_ENDPOINT = "https://rs.alarmnet.com/TC21api/tc2.asmx?WSDL"
    API_APP_ID = "14588"
    API_APP_VERSION = "1.0.34"

    def request(self, operation_name, args, attempts_remaining=5):
        """Send a SOAP request. args is a list or tuple defining the
        parameters to the operation.
        """
        is_first_request = attempts_remaining == 5
        attempts_remaining -= 1
        if not self.soap_client:
            transport = zeep.transports.Transport(
                cache=zeep.cache.InMemoryCache(timeout=3600),
                timeout=self.TIMEOUT,  # for loading WSDL and xsd documents
                operation_timeout=self.TIMEOUT,  # for operations (POST/GET)
            )
            self.soap_client = zeep.Client(self.API_ENDPOINT, transport=transport)
        try:
            response = self._send_one_request(operation_name, args)
            self._raise_for_retry(response)
            return response
        # To retry an exception that could be raised during the
        # request, add it to an except block here, depending on what
        # you want to have happen. The first block just retries and
        # logs. The second block causes reauthentication.
        except (RetryableTotalConnectError, requests.exceptions.RequestException) as err:
            if attempts_remaining <= 0:
                raise
            if isinstance(err, RetryableTotalConnectError):
                msg = f"{self.username} {operation_name}{args} {err.args[0]} on response"
            else:
                msg = f"{self.username} {operation_name}{args} {err} on request"
            if is_first_request:
                LOGGER.info(f"{msg}: {attempts_remaining} retries remaining")
            else:
                LOGGER.debug(f"{msg}: {attempts_remaining} retries remaining")
            time.sleep(self.retry_delay)
        except ZeepFault as err:
            if attempts_remaining <= 0:
                raise ServiceUnavailable(f"Error connecting to Total Connect service: {err}") from err
            LOGGER.debug(f"Error connecting to Total Connect service: {attempts_remaining} retries remaining")
            time.sleep(self.retry_delay)
        except InvalidSessionError as err:
            if attempts_remaining <= 0:
                raise ServiceUnavailable(f"Invalid Session after multiple retries: {err}") from err
            LOGGER.info(f"reauthenticating {self.username}: {attempts_remaining} retries remaining")
            old_token = self.token
            self.token = None
            self.authenticate()
            args = [self.token if old_token == arg else arg for arg in args]
        return self.request(operation_name, args, attempts_remaining)

    def authenticate(self):
        """Login to the system. Upon success, self.token is a valid credential
        for further API calls, and self._user and self.locations are valid.
        self.locations will not be refreshed if it was non-empty on entry.
        """
        start_time = time.time()
        if self._invalid_credentials:
            raise AuthenticationError(
                f"not authenticating: password already failed for user {self.username}"
            )

        # LoginAndGetSessionDetails is very slow, so only use it when necessary
        operation_name = (
            "AuthenticateUserLogin" if self._locations else "LoginAndGetSessionDetails"
        )
        response = self.request(operation_name, (
            self.username, self.password, self.API_APP_ID, self.API_APP_VERSION
        ))
        try:
            self.raise_for_resultcode(response)
        except AuthenticationError:
            self._invalid_credentials = True
            self.token = None
            raise

        self.token = response["SessionID"]
        if not self._locations:
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

    def validate_usercode(self, device_id, usercode):
        """Return True if the usercode is valid for the device."""
        response = self.request("ValidateUserCode", (self.token, device_id, str(usercode)))
        try:
            self.raise_for_resultcode(response)
        except UsercodeInvalid:
            LOGGER.warning(f"usercode {usercode} invalid for device {device_id}")
            return False
        except UsercodeUnavailable:
            LOGGER.warning(f"usercode {usercode} unavailable for device {device_id}")
            return False
        return True

    def is_logged_in(self):
        """Return true if the client is logged into the Total Connect service
        with valid credentials.
        """
        return self.token is not None

    def log_out(self):
        """Upon return, we are logged out. Raises TotalConnectError if we
        still might be logged in.
        """
        if self.is_logged_in():
            response = self.request("Logout", (self.token,))
            self.raise_for_resultcode(response)
            LOGGER.info("Logout Successful")
            self.token = None

    def get_number_locations(self):
        """Return the number of locations.  Home Assistant needs a way
        to force the locations to load inside a callable function.
        """
        return len(self.locations)

    def _make_locations(self, response):
        """Return a dict mapping LocationID to TotalConnectLocation."""
        start_time = time.time()
        new_locations = {}

        for locationinfo in (response["Locations"] or {}).get("LocationInfoBasic", {}):
            location_id = locationinfo["LocationID"]
            location = TotalConnectLocation(locationinfo, self)
            new_locations[location_id] = location

            location.auto_bypass_low_battery = self.auto_bypass_low_battery

            # set the usercode for the location
            usercode = (
                self.usercodes.get(location_id) or  # noqa: W504
                self.usercodes.get(str(location_id)) or self.usercodes.get("default")
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

    def __init__(self, partition_or_location):
        self.armable = partition_or_location

    def arm_away(self):
        """Arm the system (Away)."""
        self.armable.arm(ArmType.AWAY)

    def arm_stay(self):
        """Arm the system (Stay)."""
        self.armable.arm(ArmType.STAY)

    def arm_stay_instant(self):
        """Arm the system (Stay - Instant)."""
        self.armable.arm(ArmType.STAY_INSTANT)

    def arm_away_instant(self):
        """Arm the system (Away - Instant)."""
        self.armable.arm(ArmType.AWAY_INSTANT)

    def arm_stay_night(self):
        """Arm the system (Stay - Night)."""
        self.armable.arm(ArmType.STAY_NIGHT)

    def disarm(self):
        self.armable.disarm()
