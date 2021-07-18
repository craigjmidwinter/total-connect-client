"""TotalConnectClient() in this file is the primary class of this package.
Instantiate it like this:

usercodes = { 'default': '1234' }
client = TCC.TotalConnectClient(username, password, usercodes)

for location in client.locations:
    ### do stuff with this location
"""

import logging
import time
import warnings

import zeep

from location import TotalConnectLocation
from user import TotalConnectUser
from exceptions import (
    TotalConnectError, AuthenticationError, InvalidSessionError,
    BadResultCodeError, RetryableTotalConnectError,
)

PROJECT_URL = "https://github.com/craigjmidwinter/total-connect-client"

ARM_TYPE_AWAY = 0
ARM_TYPE_STAY = 1
ARM_TYPE_STAY_INSTANT = 2
ARM_TYPE_AWAY_INSTANT = 3
ARM_TYPE_STAY_NIGHT = 4

RESULT_SUCCESS = 0

GET_ALL_SENSORS_MASK_STATUS_SUCCESS = 0

DEFAULT_USERCODE = "-1"

LOGGER = logging.getLogger(__name__)


class TotalConnectClient:
    """Client for Total Connect."""

    INVALID_SESSION = -102
    SUCCESS = 0
    ARM_SUCCESS = 4500
    DISARM_SUCCESS = 4500
    SESSION_INITIATED = 4500
    CONNECTION_ERROR = 4101
    FAILED_TO_CONNECT = -4104
    USER_CODE_INVALID = -4106
    USER_CODE_UNAVAILABLE = -4114
    COMMAND_FAILED = -4502
    BAD_USER_OR_PASSWORD = -50004
    AUTHENTICATION_FAILED = -100
    FEATURE_NOT_SUPPORTED = -120

    MAX_RETRY_ATTEMPTS = 10

    def __init__(
        self,
        username,
        password,
        usercodes=None,
        auto_bypass_battery=False,
        retry_delay=3,  # seconds between retries
    ):
        """Initialize."""
        self.times = {}
        self.time_start = time.time()
        self.soap_client = None
        self.application_id = "14588"
        self.application_version = "1.0.34"

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

    def get_times(self):
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
        rc = response["ResultCode"]
        if rc == self.INVALID_SESSION:
            raise InvalidSessionError('invalid session', response)
        if rc == self.CONNECTION_ERROR:
            raise RetryableTotalConnectError('connection error', response)
        if rc == self.FAILED_TO_CONNECT:
            raise RetryableTotalConnectError('failed to connect with panel', response)

    def raise_for_resultcode(self, response):
        """If response.ResultCode indicates success, return and do nothing.
        If it indicates an authentication error, raise AuthenticationError.
        """
        rc = response["ResultCode"]
        if rc in (
                self.SUCCESS,
                self.ARM_SUCCESS,
                self.DISARM_SUCCESS,
                self.SESSION_INITIATED,
        ):
            return
        self._raise_for_retry(response)
        if rc == self.COMMAND_FAILED:
            raise BadResultCodeError('command failed', response)
        if rc == self.FEATURE_NOT_SUPPORTED:
            raise BadResultCodeError('feature not supported', response)
        if rc == self.USER_CODE_INVALID:
            raise BadResultCodeError('user code invalid', response)
        if rc == self.BAD_USER_OR_PASSWORD:
            raise AuthenticationError('bad user or password', response)
        if rc == self.AUTHENTICATION_FAILED:
            raise AuthenticationError('authentication failed', response)
        if rc == self.USER_CODE_UNAVAILABLE:
            # FIXME: why is this an AuthError but USER_CODE_INVALID isn't?
            raise AuthenticationError('user code unavailable', response)
        raise BadResultCodeError(f'unknown result code {rc}', response)

    def request(self, request, attempts=0):
        """Send a SOAP request."""

        if not self.soap_client:
            self.soap_client = zeep.Client("https://rs.alarmnet.com/TC21api/tc2.asmx?WSDL")
        try:
            LOGGER.debug(f"sending API request {request}")
            r = eval("self.soap_client.service." + request)
            response = zeep.helpers.serialize_object(r)
            self._raise_for_retry(response)
            return response
        except RetryableTotalConnectError as err:
            if attempts > self.MAX_RETRY_ATTEMPTS:
                raise
            LOGGER.info(f"retrying {err.args[0]}, attempt # {attempts}")
            time.sleep(self.retry_delay)
            return self.request(request, attempts + 1)
        except InvalidSessionError:
            if attempts > self.MAX_RETRY_ATTEMPTS:
                raise
            LOGGER.info(f"reauthenticating session, attempt # {attempts}")
            self.token = None
            self.authenticate()
            return self.request(request, attempts + 1)

    def authenticate(self):
        """Login to the system. Upon success, self.token is a valid credential
        for further API calls, and self._user and self.locations are valid.
        self.locations will not be refreshed if it was non-empty on entry.
        """
        start_time = time.time()
        if self._invalid_credentials:
            raise AuthenticationError(
                f"not authenticating: password already failed for user {self.username}")

        # LoginAndGetSessionDetails is very slow, so only use it when necessary
        verb = "AuthenticateUserLogin" if self._locations else "LoginAndGetSessionDetails"
        response = self.request(
            verb + "(self.username, self.password, "
            "self.application_id, self.application_version)"
        )
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
        response = self.request(
            f"ValidateUserCode(self.token, {device_id}, '{usercode}')"
        )

        if response["ResultCode"] in (self.USER_CODE_INVALID, self.USER_CODE_UNAVAILABLE):
            LOGGER.warning(f"usercode {usercode} invalid for device {device_id}")
            return False
        self.raise_for_resultcode(response)
        return True

    def is_logged_in(self):
        """Return true if the client is logged into Total Connect service."""
        return self.token is not None

    def log_out(self):
        """Upon return, we are logged out. Raises TotalConnectError if we
        still might be logged in.
        """
        if self.is_logged_in():
            response = self.request("Logout(self.token)")
            self.raise_for_resultcode(response)
            LOGGER.info("Logout Successful")
            self.token = None

    def is_valid_credentials(self):
        """Return True if the credentials are known to be valid."""
        return self.token is not None

    def _make_locations(self, response):
        """Return a dict mapping LocationID to TotalConnectLocation."""
        start_time = time.time()
        new_locations = {}

        for location in (response["Locations"] or {}).get("LocationInfoBasic", {}):
            location_id = location["LocationID"]
            new_locations[location_id] = TotalConnectLocation(location, self)

            # set auto_bypass
            new_locations[location_id].auto_bypass_low_battery = self.auto_bypass_low_battery

            # set the usercode for the location
            usercode = (self.usercodes.get(location_id) or
                        self.usercodes.get(str(location_id)) or
                        self.usercodes.get('default'))
            if usercode:
                new_locations[location_id].usercode = usercode
            else:
                LOGGER.warning(f"no usercode for location {location_id}")
                new_locations[location_id].usercode = DEFAULT_USERCODE

        self.times["_make_locations()"] = time.time() - start_time
        return new_locations

    def keep_alive(self):
        """Keep the token alive to avoid server timeouts."""
        # TODO: why, if we're making a server round trip, are we doing nothing
        # instead of updating some status?
        LOGGER.debug("keep_alive()")

        response = self.soap_client.service.KeepAlive(self.token)
        if response.ResultCode != self.SUCCESS:
            self.authenticate()

    def arm_away(self, location_id):
        """Arm the system (Away)."""
        warnings.warn(
            "Using deprecated client.arm_away(). " "Use location.arm_away().",
            DeprecationWarning,
        )
        return self.arm(ARM_TYPE_AWAY, location_id)

    def arm_stay(self, location_id):
        """Arm the system (Stay)."""
        warnings.warn(
            "Using deprecated client.arm_stay(). " "Use location.arm_stay().",
            DeprecationWarning,
        )
        return self.arm(ARM_TYPE_STAY, location_id)

    def arm_stay_instant(self, location_id):
        """Arm the system (Stay - Instant)."""
        warnings.warn(
            "Using deprecated client.arm_stay_instant(). "
            "Use location.arm_stay_instant().",
            DeprecationWarning,
        )
        return self.arm(ARM_TYPE_STAY_INSTANT, location_id)

    def arm_away_instant(self, location_id):
        """Arm the system (Away - Instant)."""
        warnings.warn(
            "Using deprecated client.arm_away_instant(). "
            "Use location.arm_away_instant().",
            DeprecationWarning,
        )
        return self.arm(ARM_TYPE_AWAY_INSTANT, location_id)

    def arm_stay_night(self, location_id):
        """Arm the system (Stay - Night)."""
        warnings.warn(
            "Using deprecated client.arm_stay_night(). "
            "Use location.arm_stay_night().",
            DeprecationWarning,
        )
        return self.arm(ARM_TYPE_STAY_NIGHT, location_id)

    def arm(self, arm_type, location_id):
        """Arm the system. Return True if successful."""
        warnings.warn(
            "Using deprecated client.arm(). " "Use location.arm().", DeprecationWarning
        )
        return self.locations[location_id].arm(arm_type)

    def arm_custom(self, arm_type, location_id):
        """Arm custom the system."""
        ZONE_INFO = {"ZoneID": "12", "ByPass": False, "ZoneStatus": 0}

        ZONES_LIST = {}
        ZONES_LIST[0] = ZONE_INFO

        CUSTOM_ARM_SETTINGS = {"ArmMode": "1", "ArmDelay": "5", "ZonesList": ZONES_LIST}

        result = self.request(
            f"CustomArmSecuritySystem(self.token, "
            f"{location_id}, "
            f"{self.locations[location_id].security_device_id}, "
            f"{arm_type}, '{self.locations[location_id].usercode}', "
            f"{CUSTOM_ARM_SETTINGS})"
        )

        self.raise_for_resultcode(result)

        # remove after this is all working
        print(
            f"arm_custom ResultCode: {result['ResultCode']}. "
            f"arm_custom ResultData: {result['ResultData']}"
        )

    def get_custom_arm_settings(self, location_id):
        """Get custom arm settings.  Return true if successful."""
        warnings.warn(
            "Using deprecated client.get_custom_arm_settings(). "
            "Use location.get_custom_arm_settings().",
            DeprecationWarning,
        )
        return self.locations[location_id].get_custom_arm_settings()

    def get_panel_meta_data(self, location_id):
        """Get all meta data about the alarm panel."""
        warnings.warn(
            "Using deprecated client.get_panel_meta_data(). "
            "Use location.get_panel_meta_data().",
            DeprecationWarning,
        )
        return self.locations[location_id].get_panel_meta_data()

    def zone_status(self, location_id, zone_id):
        """Get status of a zone."""
        warnings.warn(
            "Using deprecated client.zone_status(). " "Use location.zone_status().",
            DeprecationWarning,
        )
        return self.locations[location_id].zone_status(zone_id)

    def get_armed_status(self, location_id):
        """Get the status of the panel."""
        warnings.warn(
            "Using deprecated client.zone_status(). " "Use location.zone_status().",
            DeprecationWarning,
        )
        return self.locations[location_id].get_armed_status()

    def disarm(self, location_id):
        """Disarm the system. Return True if successful."""
        warnings.warn(
            "Using deprecated client.disarm(). " "Use location.disarm().",
            DeprecationWarning,
        )
        return self.locations[location_id].disarm()

    def zone_bypass(self, zone_id, location_id):
        """Bypass a zone.  Return true if successful."""
        warnings.warn(
            "Using deprecated client.zone_bypass(). " "Use location.zone_bypass().",
            DeprecationWarning,
        )
        return self.locations[location_id].zone_bypass(zone_id)

    def get_zone_details(self, location_id):
        """Get Zone details. Return True if successful."""
        warnings.warn(
            "Using deprecated client.get_zone_details(). "
            "Use location.get_zone_details().",
            DeprecationWarning,
        )
        return self.locations[location_id].get_zone_details()
