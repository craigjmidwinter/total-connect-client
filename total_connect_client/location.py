"""Total Connect Location."""

import logging

from .device import TotalConnectDevice
from .partition import TotalConnectPartition
from .zone import TotalConnectZone
from .exceptions import PartialResponseError, TotalConnectError

ARM_TYPE_AWAY = 0
ARM_TYPE_STAY = 1
ARM_TYPE_STAY_INSTANT = 2
ARM_TYPE_AWAY_INSTANT = 3
ARM_TYPE_STAY_NIGHT = 4

DEFAULT_USERCODE = "-1"

LOGGER = logging.getLogger(__name__)


class TotalConnectLocation:
    """TotalConnectLocation class."""

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

        dib = (location_info_basic.get("DeviceList") or {}).get("DeviceInfoBasic")
        tcdevs = [TotalConnectDevice(d) for d in (dib or {})]
        self.devices = {tcdev.id: tcdev for tcdev in tcdevs}

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

    def set_zone_details(self, result):
        """
        Update from GetZonesListInStateEx_V1.
        
        ZoneStatusInfoWithPartitionId provides additional info for setting up zones.
        If we used TotalConnectZone.update() it would overwrite missing data with None.
        """
        zone_info = ((result.get("ZoneStatus") or {}).get("Zones") or {}).get("ZoneStatusInfoWithPartitionId")
        if not zone_info:
            raise PartialResponseError('no ZoneStatusInfoWithPartitionId', result)

        for zonedata in zone_info:
            self.zones[zonedata["ZoneID"]] = TotalConnectZone(zonedata)

    def get_panel_meta_data(self):
        """Get all meta data about the alarm panel."""
        # see https://rs.alarmnet.com/TC21api/tc2.asmx?op=GetPanelMetaDataAndFullStatus
        result = self.parent.request(
            f"GetPanelMetaDataAndFullStatusEx_V2(self.token, {self.location_id}, 0, 0, {self._partition_list})"
        )
        self.parent.raise_for_resultcode(result)

        self.set_status(result)
        self.update_partitions(result)
        self.update_zones(result)


    def set_status(self, result):
        """Update from result."""
        data = (result or {}).get("PanelMetadataAndStatus")
        if not data:
            raise PartialResponseError('no PanelMetadataAndStatus', result)

        self.ac_loss = data.get("IsInACLoss")
        self.low_battery = data.get("IsInLowBattery")
        self.cover_tampered = data.get("IsCoverTampered")
        self.last_updated_timestamp_ticks = data.get("LastUpdatedTimestampTicks")
        self.configuration_sequence_number = data.get("ConfigurationSequenceNumber")

        astate = result.get("ArmingState")
        if not astate:
            raise PartialResponseError('no ArmingState', result)
        self.arming_state = astate


    def get_zone_details(self):
        """Get Zone details."""
        result = self.parent.request(
            f"GetZonesListInStateEx_V1(self.token, {self.location_id}, {self._partition_list}, 0)"
        )

        if result["ResultCode"] == self.parent.FEATURE_NOT_SUPPORTED:
            LOGGER.warning(
                "getting Zone Details is a feature not supported by "
                "your Total Connect account or hardware"
            )
        self.parent.raise_for_resultcode(result)
        self.set_zone_details(result)

    def update_partitions(self, result):
        """Update partition info from Partitions."""
        pi = ((result.get("PanelMetadataAndStatus") or {}).get("Partitions") or {}).get("PartitionInfo")
        if not pi:
            raise PartialResponseError('no PartitionInfo', result)

        # loop through partitions and update
        # NOTE: do not use keys because they don't line up with PartitionID
        for partition in pi.values():
            if "PartitionID" not in partition:
                raise PartialResponseError('no PartitionID', result)
            partition_id = int(partition["PartitionID"])            
            if partition_id in self.partitions:
                self.partitions[partition_id].update(partition)
            else:
                logging.warning(f"Update provided for unknown partion {partition_id} ")

    def update_zones(self, result):
        """Update zone info from ZoneInfo or ZoneInfoEx."""

        data = (result.get("PanelMetadataAndStatus") or {}).get("Zones")
        if not data:
            LOGGER.error(
                f"no zones found: sync your panel using TotalConnect app or website"
            )
            # PartialResponseError would mean this is retryable without fixing
            # anything, and this needs fixing
            raise TotalConnectError('no zones found: panel sync required')

        zone_info = data.get("ZoneInfoEx") or data.get("ZoneInfo")
        if not zone_info:
            raise PartialResponseError('no ZoneInfoEx or ZoneInfo', result)
        for zonedata in zone_info:
            zid = (zonedata or {}).get("ZoneID")
            if not zid:
                raise PartialResponseError('no ZoneID', result)
            zone = self.zones.get(zid)
            if zone:
                zone.update(zonedata)
            else:
                zone = TotalConnectZone(zonedata)
                self.zones[zid] = zone

            if zone.is_low_battery() and self.auto_bypass_low_battery:
                self.parent.zone_bypass(zone, self.location_id)

    def get_partition_details(self):
        """Get partition details for this location."""
        # see https://rs.alarmnet.com/TC21api/tc2.asmx?op=GetPartitionsDetails

        result = self.parent.request(
            f"GetPartitionsDetails(self.token, {self.location_id}, {self.security_device_id})"
        )
        try:
            self.parent.raise_for_resultcode(result)
        except TotalConnectError:
            LOGGER.error(
                f"Could not get partition details for "
                f"device {self.security_device_id} at "
                f"location {self.location_id}."
                f"ResultCode: {result['ResultCode']}. "
                f"ResultData: {result['ResultData']}"
            )
            raise

        partition_details = ((result or {}).get("PartitionsInfoList") or {}).get("PartitionDetails")
        if not partition_details:
            raise PartialResponseError('no PartitionDetails', result)

        new_partition_list = []
        for partition in partition_details:
            new_partition = TotalConnectPartition(partition, self)
            self.partitions[new_partition.id] = new_partition
            new_partition_list.append(new_partition.id)

        self._partition_list = {"int": new_partition_list}

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
        self.arm(ARM_TYPE_AWAY, partition_id)

    def arm_stay(self, partition_id=None):
        """Arm the system (Stay)."""
        self.arm(ARM_TYPE_STAY, partition_id)

    def arm_stay_instant(self, partition_id=None):
        """Arm the system (Stay - Instant)."""
        self.arm(ARM_TYPE_STAY_INSTANT, partition_id)

    def arm_away_instant(self, partition_id=None):
        """Arm the system (Away - Instant)."""
        self.arm(ARM_TYPE_AWAY_INSTANT, partition_id)

    def arm_stay_night(self, partition_id=None):
        """Arm the system (Stay - Night)."""
        self.arm(ARM_TYPE_STAY_NIGHT, partition_id)

    def arm(self, arm_type, partition_id=None):
        """Arm the given partition."""
        # if no partition is given, arm all partitions
        # see https://rs.alarmnet.com/TC21api/tc2.asmx?op=ArmSecuritySystemPartitionsV1
        partition_list = []
        if partition_id is None:
            partition_list = self._partition_list
        else:
            if partition_id not in self.partitions:
                raise TotalConnectError(f"Partition {partition_id} does not exist "
                                        f"at location {self.location_id}")
            partition_list.append(partition_id)

        result = self.parent.request(
            f"ArmSecuritySystemPartitionsV1(self.token, "
            f"{self.location_id}, "
            f"{self.security_device_id}, "
            f"{arm_type}, "
            f"'{self.usercode}', "
            f"{partition_list})"
        )
        if result["ResultCode"] == self.parent.COMMAND_FAILED:
            LOGGER.warning("could not arm system; is a zone faulted?")
        self.parent.raise_for_resultcode(result)
        LOGGER.info(f"ARMED(type {arm_type}) partitions {partition_list} at {self.location_id}")

    def disarm(self, partition_id=None):
        """Disarm the system. Return True if successful."""
        # if no partition is given, disarm all partitions
        # see https://rs.alarmnet.com/TC21api/tc2.asmx?op=ArmSecuritySystemPartitionsV1
        partition_list = []
        if partition_id is None:
            partition_list = self._partition_list
        else:
            if partition_id not in self.partitions:
                raise TotalConnectError(f"Partition {partition_id} does not exist "
                                        f"at location {self.location_id}")
            partition_list.append(partition_id)

        result = self.parent.request(
            f"DisarmSecuritySystemPartitionsV1(self.token, "
            f"{self.location_id}, "
            f"{self.security_device_id}, "
            f"'{self.usercode}', "
            f"{partition_list})"
        )
        self.parent.raise_for_resultcode(result)
        LOGGER.info(f"DISARMED partitions {partition_list} at {self.location_id}")

    def zone_bypass(self, zone_id):
        """Bypass a zone."""
        result = self.parent.request(
            f"Bypass(self.token, "
            f"{self.location_id}, "
            f"{self.security_device_id}, "
            f"{zone_id}, "
            f"'{self.usercode}')"
        )
        self.parent.raise_for_resultcode(result)
        LOGGER.info(f"BYPASSED {zone_id} at {self.location_id}")
        self.zones[zone_id]._mark_as_bypassed()

    def zone_status(self, zone_id):
        """Get status of a zone."""
        z = self.zones.get(zone_id)
        if not z:
            raise TotalConnectError(f'zone {zone_id} does not exist')
        return z.status

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
        result = self.parent.request(
            f"GetCustomArmSettings(self.token, "
            f"{self.location_id}, "
            f"{self.security_device_id})"
        )
        self.parent.raise_for_resultcode(result)
        # FIXME: returning the raw result is not right
        return result
