"""Total Connect Client."""

import logging
import time

import zeep

from device import TotalConnectDevice
from partition import TotalConnectPartition
from user import TotalConnectUser

PROJECT_URL = "https://github.com/craigjmidwinter/total-connect-client"

ARM_TYPE_AWAY = 0
ARM_TYPE_STAY = 1
ARM_TYPE_STAY_INSTANT = 2
ARM_TYPE_AWAY_INSTANT = 3
ARM_TYPE_STAY_NIGHT = 4

RESULT_SUCCESS = 0

ZONE_STATUS_NORMAL = 0
ZONE_STATUS_BYPASSED = 1
ZONE_STATUS_FAULT = 2
ZONE_STATUS_TROUBLE = 8  # is also Tampered
ZONE_STATUS_LOW_BATTERY = 64
ZONE_STATUS_TRIGGERED = 256

ZONE_TYPE_SECURITY = 0
ZONE_TYPE_LYRIC_CONTACT = 1
ZONE_TYPE_PROA7_SECURITY = 3
ZONE_TYPE_LYRIC_MOTION = 4
ZONE_TYPE_LYRIC_POLICE = 6
ZONE_TYPE_PROA7_POLICE = 7
ZONE_TYPE_FIRE_SMOKE = 9
ZONE_TYPE_PROA7_INTERIOR_DELAY = 10
ZONE_TYPE_LYRIC_TEMP = 12
ZONE_TYPE_PROA7_FLOOD = 12
ZONE_TYPE_CARBON_MONOXIDE = 14
ZONE_TYPE_PROA7_MEDICAL = 15
ZONE_TYPE_LYRIC_LOCAL_ALARM = 89

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
            f"'{self.locations[location_id].usercode}')"
        )

        if result["ResultCode"] in (self.ARM_SUCCESS, self.SUCCESS):
            return True

        if result["ResultCode"] == self.COMMAND_FAILED:
            logging.warning("Could not arm system. Check if a zone is faulted.")
            return False

        if result["ResultCode"] in (self.USER_CODE_INVALID, self.USER_CODE_UNAVAILABLE):
            logging.warning("User code is invalid.")
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
        result = self.request(
            f"DisarmSecuritySystem(self.token, "
            f"{location_id}, "
            f"{self.locations[location_id].security_device_id}, "
            f"'{self.locations[location_id].usercode}')"
        )

        if result["ResultCode"] in (self.DISARM_SUCCESS, self.SUCCESS):
            logging.info("System Disarmed")
            return True

        if result["ResultCode"] in (self.USER_CODE_INVALID, self.USER_CODE_UNAVAILABLE):
            logging.warning("User code is invalid.")
            return False

        logging.error(
            f"Could not disarm system. "
            f"ResultCode: {result['ResultCode']}. "
            f"ResultData: {result['ResultData']}"
        )
        return False

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

    KNOWN_PANEL_STATES = [
        DISARMED,
        DISARMED_BYPASS,
        ARMED_AWAY,
        ARMED_AWAY_BYPASS,
        ARMED_AWAY_INSTANT,
        ARMED_AWAY_INSTANT_BYPASS,
        ARMED_CUSTOM_BYPASS,
        ARMED_STAY,
        ARMED_STAY_BYPASS,
        ARMED_STAY_INSTANT,
        ARMED_STAY_INSTANT_BYPASS,
        ARMED_STAY_NIGHT,
        ARMING,
        DISARMING,
        ALARMING,
        ALARMING_FIRE_SMOKE,
        ALARMING_CARBON_MONOXIDE,
    ]

    def __init__(self, location_info_basic, parent):
        """Initialize based on a 'LocationInfoBasic'."""
        self.location_id = location_info_basic["LocationID"]
        self.location_name = location_info_basic["LocationName"]
        self._photo_url = location_info_basic["PhotoURL"]
        self._module_flags = dict(
            x.split("=") for x in location_info_basic["LocationModuleFlags"].split(",")
        )
        self.security_device_id = location_info_basic["SecurityDeviceID"]
        self.parent = parent
        self.ac_loss = None
        self.low_battery = None
        self.cover_tampered = None
        self.last_updated_timestamp_ticks = None
        self.configuration_sequence_number = None
        self.arming_state = None
        self.partitions = {}
        self._partition_list = None
        self.zones = {}
        self.usercode = DEFAULT_USERCODE
        self._auto_bypass_low_battery = False

        self.devices = {}
        if "DeviceList" in location_info_basic:
            if location_info_basic["DeviceList"] is not None:
                if "DeviceInfoBasic" in location_info_basic["DeviceList"]:
                    device_info_basic = location_info_basic["DeviceList"][
                        "DeviceInfoBasic"
                    ]
                    if device_info_basic is not None:
                        for single_device in device_info_basic:
                            device = TotalConnectDevice(single_device)
                            self.devices[device.id] = device

    def __str__(self):
        """Return a text string that is printable."""
        data = (
            f"LOCATION {self.location_id} - {self.location_name}\n\n"
            f"PhotoURL: {self._photo_url}\n"
            f"SecurityDeviceID: {self.security_device_id}\n"
            f"AcLoss: {self.ac_loss}\n"
            f"LowBattery: {self.low_battery}\n"
            f"IsCoverTampered: {self.cover_tampered}\n"
            f"Arming State: {self.arming_state}\n"
            f"LocationModuleFlags:\n"
        )

        for key, value in self._module_flags.items():
            data = data + f"  {key}: {value}\n"

        data = data + "\n"

        devices = f"DEVICES: {len(self.devices)}\n\n"
        for device in self.devices:
            devices = devices + str(self.devices[device]) + "\n"

        partitions = f"PARTITIONS: {len(self.partitions)}\n\n"
        for partition in self.partitions:
            partitions = partitions + str(self.partitions[partition]) + "\n"

        zones = f"ZONES: {len(self.zones)}\n\n"
        for zone in self.zones:
            zones = zones + str(self.zones[zone])

        return data + devices + partitions + zones

    @property
    def auto_bypass_low_battery(self):
        """Return true if set to automatically bypass a low battery."""
        return self._auto_bypass_low_battery

    @auto_bypass_low_battery.setter
    def auto_bypass_low_battery(self, value: bool):
        """Set to automatically bypass a low battery."""
        self._auto_bypass_low_battery = value

    def set_zone_details(self, zone_status):
        """Update from GetZonesListInStateEx_V1. Return true if successful."""
        if zone_status is None:
            return False

        if "Zones" not in zone_status:
            return False
        if zone_status["Zones"] is None:
            return False

        zones = zone_status["Zones"]

        zone_info = zones.get("ZoneStatusInfoWithPartitionId")
        if zone_info is None:
            return False

        # probabaly shouldn't clear zones
        # self.locations[location_id].zones.clear()

        for zone in zone_info:
            self.zones[zone["ZoneID"]] = TotalConnectZone(zone)

        return True

    def get_panel_meta_data(self):
        """Get all meta data about the alarm panel."""
        # see https://rs.alarmnet.com/TC21api/tc2.asmx?op=GetPanelMetaDataAndFullStatus
        result = self.parent.request(
            f"GetPanelMetaDataAndFullStatusEx_V2(self.token, {self.location_id}, 0, 0, {self._partition_list})"
        )

        if result["ResultCode"] != RESULT_SUCCESS:
            logging.error(
                f"Could not retrieve panel meta data. "
                f"ResultCode: {result['ResultCode']}. ResultData: {result['ResultData']}"
            )
            return False

        if "PanelMetadataAndStatus" not in result:
            logging.warning("Panel_meta_data is empty.")
            return False

        if not self.set_status(result["PanelMetadataAndStatus"]):
            return False

        if "ArmingState" not in result:
            logging.warning(
                "GetPanelMetaDataAndFullStatus result does not contain ArmingState."
            )
            return False

        return self.set_arming_state(result["ArmingState"])

    def set_arming_state(self, new_state):
        """Set arming state.  True on success."""
        if new_state is None:
            return False

        if new_state not in self.KNOWN_PANEL_STATES:
            logging.warning(f"Security panel returned state '{new_state}' which is not known.  Please submit a ticket at {PROJECT_URL}")

        self.arming_state = new_state
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

        if not self.update_partitions(data["Partitions"]):
            return False

        if "Zones" not in data:
            logging.warning("Zones not found in PanelMetaDataAndStatus in set_status()")
            return False

        if not self.update_zones(data["Zones"]):
            return False

        return True

    def get_zone_details(self):
        """Get Zone details. Return True if successful."""
        result = self.parent.request(
            f"GetZonesListInStateEx_V1(self.token, {self.location_id}, {self._partition_list}, 0)"
        )

        if result["ResultCode"] == self.parent.FEATURE_NOT_SUPPORTED:
            logging.warning(
                "Getting Zone Details is a feature not supported by "
                "your Total Connect account or hardware."
            )
            return False

        if result["ResultCode"] != RESULT_SUCCESS:
            logging.error(
                f"Could not get zone details. "
                f"ResultCode: {result['ResultCode']}. ResultData: {result['ResultData']}."
            )
            return False

        if "ZoneStatus" in result:
            return self.set_zone_details(result["ZoneStatus"])

        logging.error(
            f"Could not get zone details. "
            f"ResultCode: {result['ResultCode']}. ResultData: {result['ResultData']}."
        )
        return False

    def update_partitions(self, data):
        """Update partition info from Partitions."""
        if "PartitionInfo" not in data:
            return False

        partition_info = data["PartitionInfo"]

        if partition_info is None:
            return False

        # TODO:  next line is WRONG, need to update partion.arming_state, NOT location.arming_state
        self.arming_state = partition_info[0]["ArmingState"]
        
        # TODO:  loop through partitions and update

        return True

    def update_zones(self, data):
        """Update zone info from ZoneInfo or ZoneInfoEx."""

        if data is None:
            logging.info(
                f"total-connect-client returned zero zones. "
                f"Sync your panel using the TotalConnect app or website."
            )
            return False

        zone_info = None

        if "ZoneInfoEx" in data:
            zone_info = data["ZoneInfoEx"]
        elif "ZoneInfo" in data:
            zone_info = data["ZoneInfo"]

        if zone_info is None:
            return False

        for zone in zone_info:
            if zone["ZoneID"] in self.zones:
                self.zones[zone["ZoneID"]].update(zone)
            else:
                self.zones[zone["ZoneID"]] = TotalConnectZone(zone)

            if (
                self.zones[zone["ZoneID"]].is_low_battery()
                and self._auto_bypass_low_battery
            ):
                self.parent.zone_bypass(zone["ZoneID"], self.location_id)

        return True

    def get_partition_details(self):
        """Get partition details for this location."""
        # see https://rs.alarmnet.com/TC21api/tc2.asmx?op=GetPartitionsDetails

        result = self.parent.request(
            f"GetPartitionsDetails(self.token, {self.location_id}, {self.security_device_id})"
        )

        if result["ResultCode"] != RESULT_SUCCESS:
            logging.error(
                f"Could not get partition details for "
                f"device {self.security_device_id} at "
                f"location {self.location_id}."
                f"ResultCode: {result['ResultCode']}. "
                f"ResultData: {result['ResultData']}"
            )
            return False

        if "PartitionsInfoList" not in result:
            return False

        partition_info_list = result["PartitionsInfoList"]

        if "PartitionDetails" not in partition_info_list:
            return False

        partition_details = partition_info_list["PartitionDetails"]

        # loop through list and add partitions
        new_partition_list = []
        for partition in partition_details:
            new_partition = TotalConnectPartition(partition)
            self.partitions[new_partition.id] = new_partition
            new_partition_list.append(new_partition.id)

        self._partition_list = {"int": new_partition_list}

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

    def set_usercode(self, usercode):
        """Set the usercode. Return true if successful."""
        if self.parent.validate_usercode(self.security_device_id, usercode):
            self.usercode = usercode
            return True

        return False


class TotalConnectZone:
    """TotalConnectZone class."""

    def __init__(self, zone):
        """Initialize."""
        self.id = zone.get("ZoneID")
        self.partition = None
        self.status = None
        self.zone_type_id = None
        self.can_be_bypassed = None
        self.battery_level = None
        self.signal_strength = None
        self.sensor_serial_number = None
        self.loop_number = None
        self.response_type = None
        self.alarm_report_state = None
        self.supervision_type = None
        self.chime_state = None
        self.device_type = None
        self.update(zone)

    def update(self, zone):
        """Update the zone.  True on success."""
        if zone is None:
            return False

        if self.id != zone.get("ZoneID"):
            raise Exception(
                f"ZoneID {zone.get('ZoneID')} does not match "
                f"expected {self.id} in TotalConnectZone."
            )

        self.description = zone.get("ZoneDescription")
        self.partition = zone.get("PartitionID")
        self.status = zone.get("ZoneStatus")
        self.can_be_bypassed = zone.get("CanBeBypassed")

        if "ZoneTypeId" in zone:
            self.zone_type_id = zone["ZoneTypeId"]

        if "Batterylevel" in zone:
            self.battery_level = zone["Batterylevel"]

        if "Signalstrength" in zone:
            self.signal_strength = zone["Signalstrength"]

        if "zoneAdditionalInfo" in zone:
            info = zone["zoneAdditionalInfo"]
            if info is not None:
                self.sensor_serial_number = info.get("SensorSerialNumber")
                self.loop_number = info.get("LoopNumber")
                self.response_type = info.get("ResponseType")
                self.alarm_report_state = info.get("AlarmReportState")
                self.supervision_type = info.get("ZoneSupervisionType")
                self.chime_state = info.get("ChimeState")
                self.device_type = info.get("DeviceType")

        return True

    def __str__(self):
        """Return a string that is printable."""
        return (
            f"Zone {self.id} - {self.description}\n"
            f"  Partition: {self.partition}\t\t"
            f"Zone Type: {self.zone_type_id}\t"
            f"CanBeBypassed: {self.can_be_bypassed}\t"
            f"Status: {self.status}\n"
            f"  Battery Level: {self.battery_level}\t"
            f"Signal Stength: {self.signal_strength}\n"
            f"  Serial Number: {self.sensor_serial_number}\t"
            f"Loop: {self.loop_number}\t"
            f"Response Type: {self.response_type}\n"
            f"  Supervision Type: {self.supervision_type}\t"
            f"Alarm Report State: {self.alarm_report_state}\n"
            f"  Chime State: {self.chime_state}\t"
            f"Device Type: {self.device_type}\n\n"
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

        # as seen so far, any security zone that cannot be bypassed is a button on a panel
        if self.zone_type_id == ZONE_TYPE_SECURITY and self.can_be_bypassed == 0:
            return True

        if self.zone_type_id in (ZONE_TYPE_PROA7_MEDICAL, ZONE_TYPE_PROA7_POLICE):
            return True

        return False

    def is_type_security(self):
        """Return true if zone type is security."""
        return self.zone_type_id in (
            ZONE_TYPE_SECURITY,
            ZONE_TYPE_LYRIC_CONTACT,
            ZONE_TYPE_PROA7_SECURITY,
            ZONE_TYPE_LYRIC_MOTION,
            ZONE_TYPE_LYRIC_POLICE,
            ZONE_TYPE_PROA7_INTERIOR_DELAY,
            ZONE_TYPE_LYRIC_LOCAL_ALARM,
        )

    def is_type_motion(self):
        """Return true if zone type is motion."""
        return self.zone_type_id == ZONE_TYPE_LYRIC_MOTION

    def is_type_fire(self):
        """Return true if zone type is fire or smoke."""
        return self.zone_type_id in (ZONE_TYPE_FIRE_SMOKE, ZONE_TYPE_LYRIC_TEMP)

    def is_type_carbon_monoxide(self):
        """Return true if zone type is carbon monoxide."""
        return self.zone_type_id == ZONE_TYPE_CARBON_MONOXIDE

    def is_type_medical(self):
        """Return true if zone type is medical."""
        return self.zone_type_id == ZONE_TYPE_PROA7_MEDICAL
