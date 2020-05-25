"""Total Connect Client."""

import logging
import time

import zeep

ARM_TYPE_AWAY = 0
ARM_TYPE_STAY = 1
ARM_TYPE_STAY_INSTANT = 2
ARM_TYPE_AWAY_INSTANT = 3
ARM_TYPE_STAY_NIGHT = 4

ZONE_STATUS_NORMAL = 0
ZONE_STATUS_BYPASSED = 1
ZONE_STATUS_FAULT = 2
ZONE_STATUS_TROUBLE = 8  # is also Tampered
ZONE_STATUS_LOW_BATTERY = 64
ZONE_STATUS_TRIGGERED = 256

ZONE_TYPE_SECURITY = 0
ZONE_TYPE_FIRE_SMOKE = 9
ZONE_TYPE_CARBON_MONOXIDE = 14

ZONE_BYPASS_SUCCESS = 0
GET_ALL_SENSORS_MASK_STATUS_SUCCESS = 0


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
    CONNECTION_ERROR = 4101
    FAILED_TO_CONNECT = -4104
    USER_CODE_UNAVAILABLE = -4114
    COMMAND_FAILED = -4502
    BAD_USER_OR_PASSWORD = -50004
    AUTHENTICATION_FAILED = -100
    FEATURE_NOT_SUPPORTED = -120

    MAX_REQUEST_ATTEMPTS = 10

    def __init__(self, username, password, usercode="-1", auto_bypass_battery=False):
        """Initialize."""
        self.times = {}
        self.time_start = time.time()
        self.soapClient = zeep.Client("https://rs.alarmnet.com/TC21api/tc2.asmx?WSDL")
        self.soap_base = "self.soapClient.service."

        self.applicationId = "14588"
        self.applicationVersion = "1.0.34"
        self.username = username
        self.password = password
        self.usercode = usercode
        self.auto_bypass_low_battery = auto_bypass_battery
        self.token = False
        self._valid_credentials = (
            None  # None at start, True after login, False if login fails
        )
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
            f"Usercode: {self.usercode}\n"
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

    def request(self, request, attempts=0):
        """Send a SOAP request."""
        if attempts < self.MAX_REQUEST_ATTEMPTS:
            attempts += 1
            response = eval(self.soap_base + request)

            if response.ResultCode in (self.SUCCESS, self.FEATURE_NOT_SUPPORTED):
                return zeep.helpers.serialize_object(response)
            if response.ResultCode == self.INVALID_SESSION:
                logging.debug(
                    f"total-connect-client invalid session (attempt number {attempts})."
                )
                self.token = False
                self.authenticate_user_login()
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
        if self._valid_credentials is not False:
            start_time = time.time()
            response = self.request(
                "LoginAndGetSessionDetails(self.username, self.password, "
                "self.applicationId, self.applicationVersion)"
            )

            if response["ResultCode"] == self.SUCCESS:
                logging.debug("Login Successful")
                self.token = response["SessionID"]
                self._valid_credentials = True
                self.populate_details(response)
                self.times["authenticate()"] = time.time() - start_time
                return True

            self._valid_credentials = False
            logging.error(
                f"Unable to authenticate with Total Connect. ResultCode: "
                f"{response['ResultCode']}. ResultData: {response['ResultData']}"
            )

        logging.debug(
            "total-connect-client attempting login with known bad credentials."
        )
        self.times["authenticate()"] = time.time() - start_time
        return False

    def authenticate_user_login(self):
        """Login to the system.  Return true if successful."""
        if self._valid_credentials is not False:
            start_time = time.time()
            response = self.request(
                "AuthenticateUserLogin(self.username, self.password, "
                "self.applicationId, self.applicationVersion)"
            )

            if response["ResultCode"] == self.SUCCESS:
                logging.debug("Login Successful")
                self.token = response["SessionID"]
                self._valid_credentials = True
                self.times["authenticate_user_login()"] = time.time() - start_time
                return True

            self._valid_credentials = False
            logging.error(
                f"Unable to authenticate with Total Connect. ResultCode: "
                f"{response['ResultCode']}. ResultData: {response['ResultData']}"
            )

        logging.debug(
            "total-connect-client attempting login with known bad credentials."
        )
        self.times["authenticate_user_login()"] = time.time() - start_time
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

        self._user = total_connect_user(response["UserInfo"])

        for location in location_data:
            location_id = location["LocationID"]
            self.locations[location_id] = TotalConnectLocation(location, self)
            self.get_zone_details(location_id)
            self.get_panel_meta_data(location_id)

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
        return self.arm(ARM_TYPE_AWAY, location_id)

    def arm_stay(self, location_id):
        """Arm the system (Stay)."""
        return self.arm(ARM_TYPE_STAY, location_id)

    def arm_stay_instant(self, location_id):
        """Arm the system (Stay - Instant)."""
        return self.arm(ARM_TYPE_STAY_INSTANT, location_id)

    def arm_away_instant(self, location_id):
        """Arm the system (Away - Instant)."""
        return self.arm(ARM_TYPE_AWAY_INSTANT, location_id)

    def arm_stay_night(self, location_id):
        """Arm the system (Stay - Night)."""
        return self.arm(ARM_TYPE_STAY_NIGHT, location_id)

    def arm(self, arm_type, location_id):
        """Arm the system. Return True if successful."""
        result = self.request(
            f"ArmSecuritySystem(self.token, "
            f"{location_id}, "
            f"{self.locations[location_id].security_device_id}, "
            f"{arm_type}, "
            f"{self.usercode})"
        )

        if result["ResultCode"] in (self.ARM_SUCCESS, self.SUCCESS):
            return True

        if result["ResultCode"] == self.COMMAND_FAILED:
            logging.warning("Could not arm system. Check if a zone is faulted.")
            return False

        logging.error(
            f"Could not arm system. "
            f"ResultCode: {result['ResultCode']}. "
            f"ResultData: {result['ResultData']}"
        )
        return False

    def arm_custom(self, arm_type, location_id):
        """Arm custom the system.  Return true if successul."""
        ZONE_INFO = {"ZoneID": "12", "ByPass": False, "ZoneStatus": ZONE_STATUS_NORMAL}

        ZONES_LIST = {}
        ZONES_LIST[0] = ZONE_INFO

        CUSTOM_ARM_SETTINGS = {"ArmMode": "1", "ArmDelay": "5", "ZonesList": ZONES_LIST}

        result = self.request(
            f"CustomArmSecuritySystem(self.token, "
            f"{location_id}, "
            f"{self.locations[location_id].security_device_id}, "
            f"{arm_type}, {self.usercode}, "
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
        """Get custom arm settings.  Return true if successul."""
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
        start_time = time.time()
        result = self.request(
            f"GetPanelMetaDataAndFullStatus(self.token, {location_id}, 0, 0, 1)"
        )

        if result["ResultCode"] != self.SUCCESS:
            logging.error(
                f"Could not retrieve panel meta data. "
                f"ResultCode: {result['ResultCode']}. ResultData: {result['ResultData']}"
            )
            return False

        if "PanelMetadataAndStatus" in result:
            status = self.locations[location_id].set_status(
                result["PanelMetadataAndStatus"]
            )
            self.times[f"get_panel_meta_data({location_id})"] = time.time() - start_time
            return status
        else:
            logging.warning("Panel_meta_data is empty.")

        self.times[f"get_panel_meta_data({location_id})"] = time.time() - start_time
        return result

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
        result = self.request(
            f"DisarmSecuritySystem(self.token, "
            f"{location_id}, "
            f"{self.locations[location_id].security_device_id}, "
            f"{self.usercode})"
        )

        if result["ResultCode"] in (self.DISARM_SUCCESS, self.SUCCESS):
            logging.info("System Disarmed")
            return True

        logging.error(
            f"Could not disarm system. "
            f"ResultCode: {result['ResultCode']}. "
            f"ResultData: {result['ResultData']}"
        )
        return False

    def zone_bypass(self, zone_id, location_id):
        """Bypass a zone."""
        response = self.soapClient.service.Bypass(
            self.token,
            location_id,
            self.locations[location_id].security_device_id,
            zone_id,
            self.usercode,
        )

        if response.ResultCode == self.INVALID_SESSION:
            self.authenticate()
            response = self.soapClient.service.Bypass(
                self.token,
                location_id,
                self.locations[location_id].security_device_id,
                zone_id,
                self.usercode,
            )

        logging.info(f"Bypass Result Code: {response.ResultCode}.")

        if response.ResultCode == ZONE_BYPASS_SUCCESS:
            self.locations[location_id].zones[zone_id].bypass()
        else:
            raise Exception(
                "Could not bypass zone. ResultCode: "
                + str(response.ResultCode)
                + ". ResultData: "
                + str(response.ResultData)
            )

        return self.SUCCESS

    def get_zone_details(self, location_id):
        """Get Zone details. Return True if successful."""
        start_time = time.time()
        result = self.request(
            "GetZonesListInStateEx_V1(self.token, "
            + str(location_id)
            + ', {"int": ["1"]}, 0)'
        )

        if result["ResultCode"] == self.FEATURE_NOT_SUPPORTED:
            logging.warning(
                "Getting Zone Details is a feature not supported by "
                "your Total Connect account or hardware."
            )
            self.times[f"get_zone_details({location_id})"] = time.time() - start_time
            return False

        if result["ResultCode"] != self.SUCCESS:
            logging.error(
                f"Could not get zone details. "
                f"ResultCode: {result['ResultCode']}. ResultData: {result['ResultData']}."
            )
            self.times[f"get_zone_details({location_id})"] = time.time() - start_time
            return False

        zone_status = result.get("ZoneStatus")
        if zone_status is not None:
            self.times[f"get_zone_details({location_id})"] = time.time() - start_time
            return self.locations[location_id].set_zone_details(zone_status)

        logging.error(
            f"Could not get zone details. "
            f"ResultCode: {result['ResultCode']}. ResultData: {result['ResultData']}."
        )
        self.times[f"get_zone_details({location_id})"] = time.time() - start_time
        return True


class TotalConnectLocation:
    """TotalConnectLocation class."""

    DISARMED = 10200
    DISARMED_BYPASS = 10211
    ARMED_AWAY = 10201
    ARMED_AWAY_BYPASS = 10202
    ARMED_AWAY_INSTANT = 10205
    ARMED_AWAY_INSTANT_BYPASS = 10206
    ARMED_CUSTOM_BYPASS = 10223
    ARMED_STAY = 10203
    ARMED_STAY_BYPASS = 10204
    ARMED_STAY_INSTANT = 10209
    ARMED_STAY_INSTANT_BYPASS = 10210
    ARMED_STAY_NIGHT = 10218
    ARMING = 10307
    DISARMING = 10308
    ALARMING = 10207
    ALARMING_FIRE_SMOKE = 10212
    ALARMING_CARBON_MONOXIDE = 10213

    def __init__(self, location_info_basic, parent):
        """Initialize based on a 'LocationInfoBasic'."""
        self.location_id = location_info_basic["LocationID"]
        self.location_name = location_info_basic["LocationName"]
        self._photo_url = location_info_basic["PhotoURL"]
        self._module_flags = dict(
            x.split("=") for x in location_info_basic["LocationModuleFlags"].split(",")
        )
        self.security_device_id = location_info_basic["SecurityDeviceID"]
        self._device_list = location_info_basic["DeviceList"]
        self.parent = parent
        self.ac_loss = None
        self.low_battery = None
        self.cover_tampered = None
        self.last_updated_timestamp_ticks = None
        self.configuration_sequence_number = None
        self.arming_state = None
        self.zones = {}

    def __str__(self):
        """Return a text string that is printable."""
        data = (
            f"LOCATION {self.location_id} - {self.location_name}\n\n"
            f"PhotoURL: {self._photo_url}\n"
            f"SecurityDeviceID: {self.security_device_id}\n"
            f"DeviceList: {self._device_list}\n"
            f"AcLoss: {self.ac_loss}\n"
            f"LowBattery: {self.low_battery}\n"
            f"IsCoverTampered: {self.cover_tampered}\n"
            f"Arming State: {self.arming_state}\n"
            f"LocationModuleFlags:\n"
        )

        for key, value in self._module_flags.items():
            data = data + f"  {key}: {value}\n"

        data = data + "\n"

        zones = f"ZONES: {len(self.zones)}\n\n"
        for zone in self.zones:
            zones = zones + str(self.zones[zone])

        return data + zones

    def set_zone_details(self, zone_status):
        """Update from GetZonesListInStateEx_V1. Return true if successful."""
        zones = zone_status.get("Zones")
        if zones is None:
            return False

        zone_info = zones.get("ZoneStatusInfoWithPartitionId")
        if zone_info is None:
            return False

        # probabaly shouldn't clear zones
        # self.locations[location_id].zones.clear()

        for zone in zone_info:
            self.zones[zone["ZoneID"]] = TotalConnectZone(zone)

        return True

    def set_status(self, data):
        """Update from 'PanelMetadataAndStatus'. Return true on success."""
        if data is None:
            return False

        self.ac_loss = data.get("IsInACLoss")
        self.low_battery = data.get("IsInLowBattery")
        self.cover_tampered = data.get("IsCoverTampered")
        self.last_updated_timestamp_ticks = data.get("LastUpdatedTimestampTicks")
        self.configuration_sequence_number = data.get("ConfigurationSequenceNumber")

        if "Partitions" not in data:
            return False

        if "PartitionInfo" not in data["Partitions"]:
            return False

        self.arming_state = data["Partitions"]["PartitionInfo"][0]["ArmingState"]

        if "Zones" not in data:
            return False

        if "ZoneInfo" not in data["Zones"]:
            return False

        for zone in data["Zones"]["ZoneInfo"]:
            if zone["ZoneID"] in self.zones:
                self.zones[zone["ZoneID"]].update(zone)
            else:
                self.zones[zone["ZoneID"]] = TotalConnectZone(zone)

            if (
                self.zones[zone["ZoneID"]].is_low_battery()
                and self.parent.auto_bypass_low_battery
            ):
                self.parent.zone_bypass(zone["ZoneID"], self.location_id)

        return True

    def is_low_battery(self):
        """Return true if low battery."""
        return self.low_battery is True

    def is_ac_loss(self):
        """Return true if AC loss."""
        return self.ac_loss is True

    def is_cover_tampered(self):
        """Return true if cover is tampered."""
        return self.cover_tampered is True

    def is_arming(self):
        """Return true if the system is in the process of arming."""
        return self.arming_state == self.ARMING

    def is_disarming(self):
        """Return true if the system is in the process of disarming."""
        return self.arming_state == self.DISARMING

    def is_pending(self):
        """Return true if the system is pending an action."""
        return self.is_disarming() or self.is_arming()

    def is_disarmed(self):
        """Return True if the system is disarmed."""
        return self.arming_state in (self.DISARMED, self.DISARMED_BYPASS)

    def is_armed_away(self):
        """Return True if the system is armed away in any way."""
        return self.arming_state in (
            self.ARMED_AWAY,
            self.ARMED_AWAY_BYPASS,
            self.ARMED_AWAY_INSTANT,
            self.ARMED_AWAY_INSTANT_BYPASS,
        )

    def is_armed_custom_bypass(self):
        """Return True if the system is armed custom bypass in any way."""
        return self.arming_state == self.ARMED_CUSTOM_BYPASS

    def is_armed_home(self):
        """Return True if the system is armed home/stay in any way."""
        return self.arming_state in (
            self.ARMED_STAY,
            self.ARMED_STAY_BYPASS,
            self.ARMED_STAY_INSTANT,
            self.ARMED_STAY_INSTANT_BYPASS,
            self.ARMED_STAY_NIGHT,
        )

    def is_armed_night(self):
        """Return True if the system is armed night in any way."""
        return self.arming_state == self.ARMED_STAY_NIGHT

    def is_armed(self):
        """Return True if the system is armed in any way."""
        return (
            self.is_armed_away()
            or self.is_armed_custom_bypass()
            or self.is_armed_home()
            or self.is_armed_night()
        )

    def is_triggered_police(self):
        """Return True if the system is triggered for police or medical."""
        return self.arming_state == self.ALARMING

    def is_triggered_fire(self):
        """Return True if the system is triggered for fire or smoke."""
        return self.arming_state == self.ALARMING_FIRE_SMOKE

    def is_triggered_gas(self):
        """Return True if the system is triggered for carbon monoxide."""
        return self.arming_state == self.ALARMING_CARBON_MONOXIDE

    def is_triggered(self):
        """Return True if the system is triggered in any way."""
        return (
            self.is_triggered_fire()
            or self.is_triggered_gas()
            or self.is_triggered_police()
        )


class TotalConnectZone:
    """TotalConnectZone class."""

    def __init__(self, zone):
        """Initialize."""
        self.id = zone.get("ZoneID")
        self.description = zone.get("ZoneDescription")
        self.status = zone.get("ZoneStatus")
        self.partition = zone.get("PartitionID")
        self.zone_type_id = zone.get("ZoneTypeId")
        self.can_be_bypassed = zone.get("CanBeBypassed")

    def update(self, zone):
        """Update the zone."""
        if self.id == zone.get("ZoneID"):
            self.description = zone.get("ZoneDescription")
            self.partition = zone.get("PartitionID")
            self.status = zone.get("ZoneStatus")
        else:
            raise Exception("ZoneID does not match in TotalConnectZone.")

    def __str__(self):
        """Return a string that is printable."""
        return (
            f"Zone {self.id} - {self.description}\n"
            f"Partition: {self.partition}\t"
            f"Type: {self.zone_type_id}\t"
            f"Status: {self.status}\n\n"
        )

    def is_bypassed(self):
        """Return true if the zone is bypassed."""
        return self.status & ZONE_STATUS_BYPASSED > 0

    def bypass(self):
        """Set is_bypassed status."""
        self.status = ZONE_STATUS_BYPASSED

    def is_faulted(self):
        """Return true if the zone is faulted."""
        return self.status & ZONE_STATUS_FAULT > 0

    def is_tampered(self):
        """Return true if zone is tampered."""
        return self.status & ZONE_STATUS_TROUBLE > 0

    def is_low_battery(self):
        """Return true if low battery."""
        return self.status & ZONE_STATUS_LOW_BATTERY > 0

    def is_troubled(self):
        """Return true if zone is troubled."""
        return self.status & ZONE_STATUS_TROUBLE > 0

    def is_triggered(self):
        """Return true if zone is triggered."""
        return self.status & ZONE_STATUS_TRIGGERED > 0

    def is_type_button(self):
        """Return true if zone is a button."""
        return self.zone_type_id == ZONE_TYPE_SECURITY and self.can_be_bypassed == 0

    def is_type_security(self):
        """Return true if zone type is security."""
        return self.zone_type_id == ZONE_TYPE_SECURITY

    def is_type_fire(self):
        """Return true if zone type is fire or smoke."""
        return self.zone_type_id == ZONE_TYPE_FIRE_SMOKE

    def is_type_carbon_monoxide(self):
        """Return true if zone type is carbon monoxide."""
        return self.zone_type_id == ZONE_TYPE_CARBON_MONOXIDE


class total_connect_user:
    """User for Total Connect."""

    def __init__(self, user_info):
        """Initialize based on UserInfo from LoginAndGetSessionDetails."""
        self._user_id = user_info["UserID"]
        self._username = user_info["Username"]
        self._features = dict(
            x.split("=") for x in user_info["UserFeatureList"].split(",")
        )
        self._master_user = self._features["Master"] == "1"
        self._user_admin = self._features["User Administration"] == "1"
        self._config_admin = self._features["Configuration Administration"] == "1"

        if self.security_problem():
            logging.warning(
                f"Total Connect user {self._username} has one or "
                "more permissions that are not necessary. Remove "
                "permissions from this user or create a new user "
                "with minimal permissions."
            )

    def security_problem(self):
        """Run security checks. Return true if problem."""
        problem = False

        if self._master_user:
            logging.warning(f"User {self._username} is a master user.")
            problem = True

        if self._user_admin:
            logging.warning(f"User {self._username} is a user administrator.")
            problem = True

        if self._config_admin:
            logging.warning(
                f"User {self._username} " "is a configuration administrator."
            )
            problem = True

        return problem

    def __str__(self):
        """Return a string that is printable."""
        data = (
            f"Username: {self._username}\n"
            f"UserID: {self._user_id}\n"
            f"Master User: {self._master_user}\n"
            f"User Administrator: {self._user_admin}\n"
            f"Configuration Administrator: {self._config_admin}\n"
            "User features:\n"
        )

        for key, value in self._features.items():
            data = data + f"  {key}: {value}\n"

        return data + "\n"
