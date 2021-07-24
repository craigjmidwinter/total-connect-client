"""Total Connect Location."""

import logging

from device import TotalConnectDevice
from partition import TotalConnectPartition
from zone import TotalConnectZone

ARM_TYPE_AWAY = 0
ARM_TYPE_STAY = 1
ARM_TYPE_STAY_INSTANT = 2
ARM_TYPE_AWAY_INSTANT = 3
ARM_TYPE_STAY_NIGHT = 4

RESULT_SUCCESS = 0

DEFAULT_USERCODE = "-1"

LOGGER = logging.getLogger(__name__)


class TotalConnectLocation:
    """TotalConnectLocation class."""

    # Location relevant ResultCode
    SUCCESS = 0
    ARM_SUCCESS = 4500
    DISARM_SUCCESS = 4500
    COMMAND_FAILED = -4502
    USER_CODE_INVALID = -4106
    USER_CODE_UNAVAILABLE = -4114
    ZONE_BYPASS_SUCCESS = 0

    # ArmingState
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
            LOGGER.error(
                f"Could not retrieve panel meta data. "
                f"ResultCode: {result['ResultCode']}. ResultData: {result['ResultData']}"
            )
            return False

        if "PanelMetadataAndStatus" not in result:
            LOGGER.warning("Panel_meta_data is empty.")
            return False

        if not self.set_status(result["PanelMetadataAndStatus"]):
            return False

        if "ArmingState" not in result:
            LOGGER.warning(
                "GetPanelMetaDataAndFullStatus result does not contain ArmingState."
            )
            return False

        return self.set_arming_state(result["ArmingState"])

    def set_arming_state(self, new_state):
        """Set arming state.  True on success."""
        if new_state is None:
            return False

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
            LOGGER.warning("Zones not found in PanelMetaDataAndStatus in set_status()")
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
            LOGGER.warning(
                "Getting Zone Details is a feature not supported by "
                "your Total Connect account or hardware."
            )
            return False

        if result["ResultCode"] != RESULT_SUCCESS:
            LOGGER.error(
                f"Could not get zone details. "
                f"ResultCode: {result['ResultCode']}. ResultData: {result['ResultData']}."
            )
            return False

        if "ZoneStatus" in result:
            return self.set_zone_details(result["ZoneStatus"])

        LOGGER.error(
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

        if not data:
            LOGGER.info(
                f"no zones found -- sync your panel using TotalConnect app or website"
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
            LOGGER.error(
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
            new_partition = TotalConnectPartition(partition, self)
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

    def arm_away(self, partition_id=None):
        """Arm the system (Away)."""
        return self.arm(ARM_TYPE_AWAY, partition_id)

    def arm_stay(self, partition_id=None):
        """Arm the system (Stay)."""
        return self.arm(ARM_TYPE_STAY, partition_id)

    def arm_stay_instant(self, partition_id=None):
        """Arm the system (Stay - Instant)."""
        return self.arm(ARM_TYPE_STAY_INSTANT, partition_id)

    def arm_away_instant(self, partition_id=None):
        """Arm the system (Away - Instant)."""
        return self.arm(ARM_TYPE_AWAY_INSTANT, partition_id)

    def arm_stay_night(self, partition_id=None):
        """Arm the system (Stay - Night)."""
        return self.arm(ARM_TYPE_STAY_NIGHT, partition_id)

    def arm(self, arm_type, partition_id=None):
        """Arm the given partition. Return True if successful."""
        # if no partition is given, arm all partitions
        # see https://rs.alarmnet.com/TC21api/tc2.asmx?op=ArmSecuritySystemPartitionsV1
        partition_list = []
        if partition_id is None:

            partition_list = self._partition_list
        else:
            if partition_id not in self.partitions:
                LOGGER.error(
                    f"Parition {partition_id} does not exist "
                    f"for location {self.location_id}."
                )
                return False

            partition_list.append(partition_id)

        result = self.parent.request(
            f"ArmSecuritySystemPartitionsV1(self.token, "
            f"{self.location_id}, "
            f"{self.security_device_id}, "
            f"{arm_type}, "
            f"'{self.usercode}', "
            f"{partition_list})"
        )

        if result["ResultCode"] in (self.ARM_SUCCESS, self.SUCCESS):
            return True

        if result["ResultCode"] == self.COMMAND_FAILED:
            LOGGER.warning("Could not arm system. Check if a zone is faulted.")
            return False

        if result["ResultCode"] in (self.USER_CODE_INVALID, self.USER_CODE_UNAVAILABLE):
            LOGGER.warning(
                f"User code {self.usercode} is invalid for location {self.location_id}."
            )
            return False

        LOGGER.error(
            f"Could not arm system. "
            f"ResultCode: {result['ResultCode']}. "
            f"ResultData: {result['ResultData']}"
        )
        return False

    def disarm(self, partition_id=None):
        """Disarm the system. Return True if successful."""
        # if no partition is given, disarm all partitions
        # see https://rs.alarmnet.com/TC21api/tc2.asmx?op=ArmSecuritySystemPartitionsV1
        partition_list = []
        if partition_id is None:

            partition_list = self._partition_list
        else:
            if partition_id not in self.partitions:
                LOGGER.error(
                    f"Parition {partition_id} does not exist "
                    f"for location {self.location_id}."
                )
                return False

            partition_list.append(partition_id)

        result = self.parent.request(
            f"DisarmSecuritySystemPartitionsV1(self.token, "
            f"{self.location_id}, "
            f"{self.security_device_id}, "
            f"'{self.usercode}', "
            f"{partition_list})"
        )

        if result["ResultCode"] in (self.DISARM_SUCCESS, self.SUCCESS):
            LOGGER.info("System Disarmed")
            return True

        if result["ResultCode"] in (self.USER_CODE_INVALID, self.USER_CODE_UNAVAILABLE):
            LOGGER.warning(
                f"User code {self.usercode} is invalid for location {self.location_id}."
            )
            return False

        LOGGER.error(
            f"Could not disarm system. "
            f"ResultCode: {result['ResultCode']}. "
            f"ResultData: {result['ResultData']}"
        )
        return False

    def zone_bypass(self, zone_id):
        """Bypass a zone.  Return true if successful."""
        result = self.parent.request(
            f"Bypass(self.token, "
            f"{self.location_id}, "
            f"{self.security_device_id}, "
            f"{zone_id}, "
            f"'{self.usercode}')"
        )

        if result["ResultCode"] is self.ZONE_BYPASS_SUCCESS:
            self.zones[zone_id].bypass()
            return True

        LOGGER.error(
            f"Could not bypass zone {zone_id} at location {self.location_id}."
            f"ResultCode: {result['ResultCode']}. "
            f"ResultData: {result['ResultData']}"
        )
        return False

    def zone_status(self, zone_id):
        """Get status of a zone."""
        z = self.zones.get(zone_id)
        if z is None:
            LOGGER.error(f"Zone {zone_id} does not exist.")
            return None

        return z.status

    def get_armed_status(self):
        """Get the status of the panel."""
        self.get_panel_meta_data()
        # TODO:  return state for the partition ???
        return self.arming_state

    def arm_custom(self, arm_type):
        """NOT OPERATIONAL YET.
        Arm custom the system.  Return true if successful.
        """
        ZONE_INFO = {"ZoneID": "12", "ByPass": False, "ZoneStatus": 0}

        ZONES_LIST = {}
        ZONES_LIST[0] = ZONE_INFO

        CUSTOM_ARM_SETTINGS = {"ArmMode": "1", "ArmDelay": "5", "ZonesList": ZONES_LIST}

        result = self.request(
            f"CustomArmSecuritySystem(self.token, "
            f"{self.location_id}, "
            f"{self.security_device_id}, "
            f"{arm_type}, '{self.usercode}', "
            f"{CUSTOM_ARM_SETTINGS})"
        )

        if result["ResultCode"] != self.SUCCESS:
            LOGGER.error(
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

    def get_custom_arm_settings(self):
        """NOT OPERATIONAL YET.
        Get custom arm settings.
        """
        result = self.request(
            f"GetCustomArmSettings(self.token, "
            f"{self.location_id}, "
            f"{self.security_device_id})"
        )

        if result["ResultCode"] != self.SUCCESS:
            LOGGER.error(
                f"Could not arm custom. ResultCode: {result['ResultCode']}. "
                f"ResultData: {result['ResultData']}"
            )
            return False

        return result
