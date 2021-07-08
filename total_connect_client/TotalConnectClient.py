"""Total Connect Client."""

import logging
import time

import zeep

from location import TotalConnectLocation
from user import TotalConnectUser

PROJECT_URL = "https://github.com/craigjmidwinter/total-connect-client"

ARM_TYPE_AWAY = 0
ARM_TYPE_STAY = 1
ARM_TYPE_STAY_INSTANT = 2
ARM_TYPE_AWAY_INSTANT = 3
ARM_TYPE_STAY_NIGHT = 4

RESULT_SUCCESS = 0

ZONE_BYPASS_SUCCESS = 0
GET_ALL_SENSORS_MASK_STATUS_SUCCESS = 0

DEFAULT_USERCODE = "-1"


class AuthenticationError(Exception):
    """Authentication Error class."""

    def __init__(self, *args, **kwargs):
        """Initialize."""
        Exception.__init__(self, *args, **kwargs)


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

    MAX_REQUEST_ATTEMPTS = 10

    def __init__(
        self,
        username,
        password,
        usercodes={"default": DEFAULT_USERCODE},
        auto_bypass_battery=False,
    ):
        """Initialize."""
        self.times = {}
        self.time_start = time.time()
        self.soapClient = None
        self.soap_base = "self.soapClient.service."
        self.soap_ready = False

        self.application_id = "14588"
        self.application_version = "1.0.34"
        self.username = username
        self.password = password

        if not isinstance(usercodes, dict):
            self.usercodes = {"default": DEFAULT_USERCODE}
        else:
            self.usercodes = usercodes

        self.auto_bypass_low_battery = auto_bypass_battery
        self.token = False
        self._valid_credentials = (
            None  # None at start, True after login, False if login fails
        )
        self._populated = False
        self._module_flags = None
        self._user = None
        self.locations = {}
        self.authenticate()
        self.times["__init__"] = time.time() - self.time_start

    def __str__(self):
        """Return a text string that is printable."""
        data = (
            f"CLIENT\n\n"
            f"Username: {self.username}\n"
            f"Password: {self.password}\n"
            f"Usercode: {self.usercodes}\n"
            f"Auto Bypass Low Battery: {self.auto_bypass_low_battery}\n"
            f"Valid Credentials: {self._valid_credentials}\n"
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

    def setup_soap(self):
        """Set up soap for use."""
        self.soapClient = zeep.Client("https://rs.alarmnet.com/TC21api/tc2.asmx?WSDL")
        self.soap_ready = True

    def request(self, request, attempts=0):
        """Send a SOAP request."""
        if self.soap_ready is False:
            self.setup_soap()

        if attempts < self.MAX_REQUEST_ATTEMPTS:
            attempts += 1
            response = eval(self.soap_base + request)

            if response.ResultCode in (
                self.SUCCESS,
                self.FEATURE_NOT_SUPPORTED,
                self.ARM_SUCCESS,
                self.DISARM_SUCCESS,
                self.SESSION_INITIATED,
                self.USER_CODE_INVALID,
            ):
                return zeep.helpers.serialize_object(response)
            if response.ResultCode == self.INVALID_SESSION:
                logging.debug(
                    f"total-connect-client invalid session (attempt number {attempts})."
                )
                self.token = False
                self.authenticate()
                return self.request(request, attempts)
            if response.ResultCode == self.CONNECTION_ERROR:
                logging.debug(
                    f"total-connect-client connection error (attempt number {attempts})."
                )
                time.sleep(3)
                return self.request(request, attempts)
            if response.ResultCode == self.FAILED_TO_CONNECT:
                logging.debug(
                    f"total-connect-client failed to connect with security system "
                    f"(attempt number {attempts})."
                )
                time.sleep(3)
                return self.request(request, attempts)
            if response.ResultCode in (
                self.BAD_USER_OR_PASSWORD,
                self.AUTHENTICATION_FAILED,
                self.USER_CODE_UNAVAILABLE,
            ):
                logging.debug("total-connect-client authentication failed.")
                return zeep.helpers.serialize_object(response)

            logging.warning(
                f"total-connect-client unknown result code "
                f"{response.ResultCode} with message: {response.ResultData}."
            )
            return zeep.helpers.serialize_object(response)

        raise Exception(
            "total-connect-client could not execute request.  Maximum attempts tried."
        )

    def authenticate(self):
        """Login to the system and populate details.  Return true if successful."""
        start_time = time.time()
        if self._valid_credentials is not False:

            if self._populated:
                response = self.request(
                    "AuthenticateUserLogin(self.username, self.password, "
                    "self.application_id, self.application_version)"
                )
            else:
                # this request is very slow, so only use it when necessary
                response = self.request(
                    "LoginAndGetSessionDetails(self.username, self.password, "
                    "self.application_id, self.application_version)"
                )

            if response["ResultCode"] == self.SUCCESS:
                logging.debug("Login Successful")
                self.token = response["SessionID"]
                self._valid_credentials = True
                if not self._populated:
                    self.populate_details(response)
                    self._populated = True
                self.times["authenticate()"] = time.time() - start_time
                return True

            self._valid_credentials = False
            self.token = False
            logging.error(
                f"Unable to authenticate with Total Connect. ResultCode: "
                f"{response['ResultCode']}. ResultData: {response['ResultData']}"
            )

        logging.debug(
            "total-connect-client attempting login with known bad credentials."
        )
        self.times["authenticate()"] = time.time() - start_time
        return False

    def validate_usercode(self, device_id, usercode):
        """Return true if the usercode is valid for the device."""
        response = self.request(
            f"ValidateUserCode(self.token, " f"{device_id}, '{usercode}')"
        )

        if response["ResultCode"] == self.SUCCESS:
            return True

        if response["ResultCode"] in (
            self.USER_CODE_INVALID,
            self.USER_CODE_UNAVAILABLE,
        ):
            logging.warning(
                f"usercode '{usercode}' " f"invalid for device {device_id}."
            )
            return False

        logging.error(
            f"Unknown response for validate_usercode. "
            f"ResultCode: {response['ResultCode']}. "
            f"ResultData: {response['ResultData']}"
        )

        return False

    def is_logged_in(self):
        """Return true if the client is logged into Total Connect service."""
        return self.token is not False

    def log_out(self):
        """Return true on logout of Total Connect service, or if not logged in."""
        if self.is_logged_in():
            response = self.request("Logout(self.token)")

            if response["ResultCode"] == self.SUCCESS:
                logging.info("Logout Successful")
                self.token = False
                return True

        return False

    def is_valid_credentials(self):
        """Return true if the credentials are known to be valid."""
        return self._valid_credentials is True

    def populate_details(self, response):
        """Populate system details."""
        start_time = time.time()
        location_data = response["Locations"]["LocationInfoBasic"]

        self._module_flags = dict(
            x.split("=") for x in response["ModuleFlags"].split(",")
        )

        self._user = TotalConnectUser(response["UserInfo"])

        for location in location_data:
            location_id = location["LocationID"]

            # self.locations[location_id] = TotalConnectLocation(location, self)
            new_location = TotalConnectLocation(location, self)

            # set auto_bypass
            new_location.auto_bypass_low_battery = self.auto_bypass_low_battery

            # set the usercode for the location
            if location_id in self.usercodes:
                new_location.usercode = self.usercodes[location_id]
            elif str(location_id) in self.usercodes:
                new_location.usercode = self.usercodes[str(location_id)]
            else:
                logging.warning(f"No usercode for location {location_id}.")

            new_location.get_partition_details()
            new_location.get_zone_details()
            new_location.get_panel_meta_data()
            self.locations[location_id] = new_location

        if len(self.locations) < 1:
            Exception("No locations found!")

        self.times["populate_details()"] = time.time() - start_time

    def keep_alive(self):
        """Keep the token alive to avoid server timeouts."""
        logging.info("total-connect-client initiating Keep Alive")

        response = self.soapClient.service.KeepAlive(self.token)

        if response.ResultCode != self.SUCCESS:
            self.authenticate()

        return response.ResultCode

    def arm_away(self, location_id):
        """Arm the system (Away)."""
        # DEPRECATED
        logging.debug(
            "Using deprecated client.arm_away(). "
            "Use location.arm_away()."
            )        
        return self.arm(ARM_TYPE_AWAY, location_id)

    def arm_stay(self, location_id):
        """Arm the system (Stay)."""
        # DEPRECATED
        logging.debug(
            "Using deprecated client.arm_stay(). "
            "Use location.arm_stay()."
            )
        return self.arm(ARM_TYPE_STAY, location_id)

    def arm_stay_instant(self, location_id):
        """Arm the system (Stay - Instant)."""
        # DEPRECATED
        logging.debug(
            "Using deprecated client.arm_stay_instant(). "
            "Use location.arm_stay_instant()."
            )
        return self.arm(ARM_TYPE_STAY_INSTANT, location_id)

    def arm_away_instant(self, location_id):
        """Arm the system (Away - Instant)."""
        # DEPRECATED
        logging.debug(
            "Using deprecated client.arm_away_instant(). "
            "Use location.arm_away_instant()."
            )
        return self.arm(ARM_TYPE_AWAY_INSTANT, location_id)

    def arm_stay_night(self, location_id):
        """Arm the system (Stay - Night)."""
        # DEPRECATED
        logging.debug(
            "Using deprecated client.arm_stay_night(). "
            "Use location.arm_stay_night()."
            )
        return self.arm(ARM_TYPE_STAY_NIGHT, location_id)

    def arm(self, arm_type, location_id):
        """Arm the system. Return True if successful."""
        # DEPRECATED
        logging.debug(
            "Using deprecated client.arm(). "
            "Use location.arm()."
            )
        return self.locations[location_id].arm(arm_type)

    def arm_custom(self, arm_type, location_id):
        """Arm custom the system.  Return true if successul."""
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

        if result["ResultCode"] != self.SUCCESS:
            logging.error(
                f"Could not arm custom. ResultCode: {result['ResultCode']}. "
                f"ResultData: {result['ResultData']}"
            )
            return False

        # remove after this is all working
        print(
            f"arm_custom ResultCode: {result['ResultCode']}. "
            f"arm_custom ResultData: {result['ResultData']}"
        )

        return True

    def get_custom_arm_settings(self, location_id):
        """Get custom arm settings.  Return true if successful."""
        result = self.request(
            f"GetCustomArmSettings(self.token, "
            f"{location_id}, "
            f"{self.locations[location_id].security_device_id})"
        )

        if result["ResultCode"] != self.SUCCESS:
            logging.error(
                f"Could not arm custom. ResultCode: {result['ResultCode']}. "
                f"ResultData: {result['ResultData']}"
            )
            return False

        return result

    def get_panel_meta_data(self, location_id):
        """Get all meta data about the alarm panel."""
        # DEPRECATED
        logging.debug(
            "Using deprecated client.get_panel_meta_data(). "
            "Use location.get_panel_meta_data()."
            )
        return self.locations[location_id].get_panel_meta_data()

    def zone_status(self, location_id, zone_id):
        """Get status of a zone."""
        z = self.locations[location_id].zones.get(zone_id)
        if z is None:
            logging.error(f"Zone {zone_id} does not exist.")
            return None

        return z.status

    def get_armed_status(self, location_id):
        """Get the status of the panel."""
        self.get_panel_meta_data(location_id)
        return self.locations[location_id].arming_state

    def disarm(self, location_id):
        """Disarm the system. Return True if successful."""
        # DEPRECATED
        logging.debug(
            "Using deprecated client.disarm(). "
            "Use location.disarm()."
            )
        return self.locations[location_id].disarm()


    def zone_bypass(self, zone_id, location_id):
        """Bypass a zone.  Return true if successful."""
        result = self.request(
            f"Bypass(self.token, "
            f"{location_id}, "
            f"{self.locations[location_id].security_device_id}, "
            f"{zone_id}, "
            f"'{self.locations[location_id].usercode}')"
        )

        if result["ResultCode"] is ZONE_BYPASS_SUCCESS:
            self.locations[location_id].zones[zone_id].bypass()
            return True

        logging.error(
            f"Could not bypass zone {zone_id} at location {location_id}."
            f"ResultCode: {result['ResultCode']}. "
            f"ResultData: {result['ResultData']}"
        )
        return False

    def get_zone_details(self, location_id):
        """Get Zone details. Return True if successful."""
        # DEPRECATED
        logging.debug(
            "Using deprecated client.get_zone_details(). "
            "Use location.get_zone_details()."
            )
        
        return self.locations[location_id].get_zone_details()


