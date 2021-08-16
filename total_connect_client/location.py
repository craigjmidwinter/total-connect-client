"""Total Connect Location."""

import logging

from .device import TotalConnectDevice
from .partition import Armable, TotalConnectPartition
from .zone import TotalConnectZone
from .exceptions import PartialResponseError, TotalConnectError

DEFAULT_USERCODE = "-1"

LOGGER = logging.getLogger(__name__)

class TotalConnectLocation(Armable):
    """Location class for Total Connect. To arm or disarm all the partitions at
    this location, call the methods from Armable.
    """
    # Location relevant ResultCode
    SUCCESS = 0
    ARM_SUCCESS = 4500
    DISARM_SUCCESS = 4500
    COMMAND_FAILED = -4502
    USER_CODE_INVALID = -4106
    USER_CODE_UNAVAILABLE = -4114
    ZONE_BYPASS_SUCCESS = 0

    def __init__(self, location_info_basic, parent):
        """Initialize based on a 'LocationInfoBasic'."""
        super().__init__()
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
            f"LocationModuleFlags:\n"
        ) + super().__str__()

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
        """Update from GetZonesListInStateEx_V1."""
        # TODO: why do we not use TotalConnectZone.update() ?
        zone_info = ((result.get("ZoneStatus") or {}).get("Zones") or {}).get("ZoneStatusInfoWithPartitionId")
        if not zone_info:
            raise PartialResponseError('no ZoneStatusInfoWithPartitionId', result)

        # probabaly shouldn't clear zones
        # TODO: explain why not
        # self.locations[location_id].zones.clear()

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

        astate = result.get("ArmingState")
        if not astate:
            raise PartialResponseError('no ArmingState', result)
        self.arming_state = astate

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

        # FIXME: next line is WRONG, need to update partion.arming_state, NOT location.arming_state
        self.arming_state = pi[0]["ArmingState"]

        # FIXME: loop through partitions and update

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

        # TODO: why not self._partition_list = new_partition_list ?
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

    def set_usercode(self, usercode):
        """Set the usercode. Return true if successful."""
        if self.parent.validate_usercode(self.security_device_id, usercode):
            self.usercode = usercode
            return True
        return False

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

    def get_armed_status(self):
        """Get the status of the panel."""
        # FIXME: why does this getter, but no others, fetch new state?
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
        result = self.parent.request(
            f"GetCustomArmSettings(self.token, "
            f"{self.location_id}, "
            f"{self.security_device_id})"
        )
        self.parent.raise_for_resultcode(result)
        # FIXME: returning the raw result is not right
        return result

        result = self.parent.request(
            f"DisarmSecuritySystemPartitionsV1(self.token, "
            f"{self.location_id}, "
            f"{self.security_device_id}, "
            f"'{self.usercode}', "
            f"{partition_list})"
        )
        self.parent.raise_for_resultcode(result)
        LOGGER.info(f"DISARMED partitions {partition_list} at {self.location_id}")

    def _armer_disarmer(self, arm_type, partition_id):
        """Don't call this at home! It's for internal use only.
        Call the arm() or disarm() methods in Armable instead.

        If arm_type is None, disarm; otherwise arm using the specified arm type.
        Operate on partition_id, or on all partitions if partition_id is None.
        Return True if successful.
        """
        # see https://rs.alarmnet.com/TC21api/tc2.asmx?op=ArmSecuritySystemPartitionsV1
        if partition_id is None:
            partition_list = self._partition_list
        else:
            if partition_id not in self.partitions:
                raise TotalConnectError(f"Partition {partition_id} does not exist "
                                        f"at location {self.location_id}")
            partition_list.append(partition_id)

        if arm_type is None:
            result = self.parent.request(
                f"DisarmSecuritySystemPartitionsV1(self.token, "
                f"{self.location_id}, "
                f"{self.security_device_id}, "
                f"'{self.usercode}', "
                f"{partition_list})"
            )
            self.parent.raise_for_resultcode(result)
            LOGGER.info(f"DISARMED partitions {partition_list} at {self.location_id}")
        else:
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
