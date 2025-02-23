"""Total Connect Location."""

import logging
from typing import Any, Dict, List

from .const import PROJECT_URL, ArmingState, ArmType, _ResultCode, make_http_endpoint
from .device import TotalConnectDevice
from .exceptions import (
    FailedToBypassZone,
    FeatureNotSupportedError,
    PartialResponseError,
    TotalConnectError,
)
from .partition import TotalConnectPartition
from .zone import TotalConnectZone, ZoneStatus

DEFAULT_USERCODE = "-1"

LOGGER = logging.getLogger(__name__)


class TotalConnectLocation:
    """TotalConnectLocation class."""

    def __init__(self, location_info_basic: Dict[str, Any], parent) -> None:
        """Initialize based on a 'LocationInfoBasic'."""
        self.location_id: int = location_info_basic["LocationID"]
        self.location_name: str = location_info_basic["LocationName"]
        self._photo_url: str = location_info_basic["PhotoURL"]
        self._module_flags = dict(
            x.split("=") for x in location_info_basic["LocationModuleFlags"].split(",")
        )
        self.security_device_id: str = location_info_basic["SecurityDeviceID"]
        self.parent = parent
        self.ac_loss = None
        self.low_battery = None
        self.cover_tampered = None
        self.last_updated_timestamp_ticks = None
        self.configuration_sequence_number = None
        self.arming_state: ArmingState = ArmingState.UNKNOWN
        self.partitions: Dict[Any, TotalConnectPartition] = {}
        self._partition_list: List[int] = []
        self.zones: Dict[Any, TotalConnectZone] = {}
        self.usercode: str = DEFAULT_USERCODE
        self.auto_bypass_low_battery: bool = False
        self._sync_job_id = None
        self._sync_job_state: int = 0

        dib = location_info_basic.get("DeviceList") or []
        tcdevs = [TotalConnectDevice(d) for d in dib]
        self.devices = {tcdev.deviceid: tcdev for tcdev in tcdevs}

    def __str__(self) -> str:  # pragma: no cover
        """Return a text string that is printable."""
        data = (
            f"LOCATION {self.location_id} - {self.location_name}\n\n"
            f"PhotoURL: {self._photo_url}\n"
            f"SecurityDeviceID: {self.security_device_id}\n"
            f"AcLoss: {self.ac_loss}\n"
            f"LowBattery: {self.low_battery}\n"
            f"IsCoverTampered: {self.cover_tampered}\n"
            f"{self.arming_state}\n"
            f"LocationModuleFlags:\n"
        )

        for key, value in self._module_flags.items():
            data = data + f"  {key}: {value}\n"

        data = data + "\n"

        devices = f"DEVICES: {len(self.devices)}\n\n"
        for device in self.devices:
            devices = devices + str(self.devices[device]) + "\n"

        partitions = f"PARTITIONS: {len(self.partitions)}\n\n"
        for status in self.partitions.values():
            partitions += str(status) + "\n"

        zones = f"ZONES: {len(self.zones)}\n\n"
        for status in self.zones.values():
            zones += str(status)

        return data + devices + partitions + zones

    def get_panel_meta_data(self) -> None:
        """Get all meta data about the alarm panel."""
        result = self.parent.http_request(
            endpoint=make_http_endpoint(
                f"api/v3/locations/{self.location_id}/partitions/fullStatus"
            ),
            method="GET",
        )
        self.parent.raise_for_resultcode(result)

        self._update_status(result)
        self._update_partitions(result["PanelStatus"]["Partitions"])
        self._update_zones(result["PanelStatus"]["Zones"])

    def get_zone_details(self) -> None:
        """Get Zone details."""
        # 0 is the ListIdentifierID, whatever that might be
        result = self.parent.http_request(
            endpoint=make_http_endpoint(
                f"api/v1/locations/{self.location_id}/partitions/zones/0"
            ),
            method="GET",
        )

        try:
            self.parent.raise_for_resultcode(result)
            self._update_zone_details(result)
        except FeatureNotSupportedError:
            LOGGER.warning(
                "getting Zone Details is a feature not supported by "
                "your Total Connect account or hardware"
            )

    def get_partition_details(self) -> None:
        """Get partition details for this location."""
        result = self.parent.http_request(
            endpoint=make_http_endpoint(
                f"api/v1/locations/{self.location_id}/devices/{self.security_device_id}/partitions/config"
            ),
            method="GET",
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

        partition_details = (result or {}).get("Partitions")
        if not partition_details:
            raise PartialResponseError("no PartitionDetails", result)

        new_partition_list = []
        for partition in partition_details:
            new_partition = TotalConnectPartition(partition, self)
            self.partitions[new_partition.partitionid] = new_partition
            new_partition_list.append(new_partition.partitionid)

        self._partition_list = new_partition_list

    def is_low_battery(self) -> bool:
        """Return true if low battery."""
        return self.low_battery is True

    def is_ac_loss(self) -> bool:
        """Return true if AC loss."""
        return self.ac_loss is True

    def is_cover_tampered(self) -> bool:
        """Return true if cover is tampered."""
        return self.cover_tampered is True

    def set_usercode(self, usercode: str) -> bool:
        """Set the usercode. Return true if successful.

        NOTE: this only sets the code in this client for this session.
        It does not save the usercode into the panel.
        """
        try:
            self.validate_usercode(usercode)
        except TotalConnectError:
            return False

        self.usercode = usercode
        return True

    def validate_usercode(self, usercode: str) -> bool:
        """Return True if the usercode is in use at location."""
        response = self.parent.http_request(
            endpoint=make_http_endpoint(
                f"api/v1/account/users/current/validateUser/locations/{self.location_id}"
            ),
            method="POST",
            data={"userCode": int(usercode)},
        )

        try:
            self.parent.raise_for_resultcode(response)
        except TotalConnectError:
            LOGGER.error(
                f"Could not validate usercode ({usercode}) "
                f"for location {self.location_id}."
                f"Response: {response}. "
            )
            raise
        return response["IsDuplicate"]

    def _build_partition_list(self, partition_id: int = 0) -> List[int]:
        """Build a list of partitions to use for arming/disarming."""
        if not partition_id:
            return self._partition_list

        if partition_id not in self.partitions:
            raise TotalConnectError(
                f"Partition {partition_id} does not exist "
                f"at location {self.location_id}"
            )
        return [partition_id]

    def arm(self, arm_type: ArmType, partition_id: int = 0, usercode: str = "") -> None:
        """Arm the given partition. If not provided, arm the location.

        If no partition is given, arm all partitions.
        If no usercode given, use stored value."""
        assert isinstance(arm_type, ArmType)
        partition_list = self._build_partition_list(partition_id)
        usercode = usercode or self.usercode
        # treats usercode as int here, but str elsewhere
        usercode = int(usercode)

        result = self.parent.http_request(
            endpoint=make_http_endpoint(
                f"api/v3/locations/{self.location_id}/devices/{self.security_device_id}/partitions/arm"
            ),
            method="PUT",
            data={
                "armType": arm_type.value,
                "userCode": usercode,
                "partitions": partition_list,
            },
        )
        if _ResultCode.from_response(result) == _ResultCode.COMMAND_FAILED:
            LOGGER.warning(
                "could not arm system; is a zone faulted?; is it already armed?"
            )
        self.parent.raise_for_resultcode(result)
        LOGGER.info(
            f"ARMED({arm_type}) partitions {partition_list} at {self.location_id}"
        )

    def disarm(self, partition_id: int = 0, usercode: str = "") -> None:
        """Disarm the system. If no partition given, disarm all of them."""
        if partition_id:
            # only check the partition
            if partition_id not in self.partitions:
                raise TotalConnectError(
                    f"Requesting to disarm unknown partition {partition_id}"
                )
            if (
                self.partitions[partition_id].arming_state.is_disarmed()
                or self.partitions[partition_id].arming_state.is_disarming()
            ):
                LOGGER.info(
                    f"Partition {partition_id} is already disarmed or in the process of disarming"
                )
                return
        else:
            # check the location
            if self.arming_state.is_disarmed() or self.arming_state.is_disarming():
                LOGGER.info(
                    f"Location {self.location_id} is already disarmed or in the process of disarming"
                )
                return

        partition_list = self._build_partition_list(partition_id)
        usercode = usercode or self.usercode
        # treats usercode as int here, but str elsewere
        usercode = int(usercode)

        result = self.parent.http_request(
            endpoint=make_http_endpoint(
                f"api/v3/locations/{self.location_id}/devices/{self.security_device_id}/partitions/disArm"
            ),
            method="PUT",
            data={"userCode": usercode, "partitions": partition_list},
        )
        self.parent.raise_for_resultcode(result)
        LOGGER.info(
            f"DISARMED partitions {partition_list} at location {self.location_id}"
        )

    def zone_bypass(self, zone_id: int) -> None:
        """Bypass a zone."""
        self._bypass_zones([zone_id])

    def zone_bypass_all(self) -> None:
        """Bypass all faulted zones."""
        faulted_zones = []
        for zone_id, zone in self.zones.items():
            if zone.is_faulted():
                faulted_zones.append(zone_id)

        self._bypass_zones(faulted_zones)

    def _bypass_zones(self, zone_list: List[int]) -> None:
        """Bypass the given list of zones."""
        if not zone_list:
            LOGGER.info("Bypass request stopped because no zones are faulted")
            return

        result = self.parent.http_request(
            endpoint=make_http_endpoint(
                f"api/v1/locations/{self.location_id}/devices/{self.security_device_id}/bypass"
            ),
            method="PUT",
            data={"ZoneIds": zone_list, "UserCode": int(self.usercode)},
        )

        if (
            self.parent.raise_for_resultcode(result)
            == _ResultCode.FAILED_TO_BYPASS_ZONE
        ):
            raise FailedToBypassZone(f"Failed to bypass zone: {result}")

        # TODO: use ZoneStatusResult to update zone status

    def clear_bypass(self) -> None:
        """Clear all bypassed zones."""
        bypassed_zones = []
        for zone_id, zone in self.zones.items():
            if zone.is_bypassed():
                bypassed_zones.append(zone_id)

        if not bypassed_zones:
            LOGGER.info("Clear bypass request stopped because no zones are bypassed")
            return

        result = self.parent.http_request(
            endpoint=make_http_endpoint(
                f"api/v2/locations/{self.location_id}/devices/{self.security_device_id}/clearBypass"
            ),
            method="PUT",
            data={"userCode": int(self.usercode)},
        )

        self.parent.raise_for_resultcode(result)

    def zone_status(self, zone_id: int) -> ZoneStatus:
        """Get status of a zone."""
        zone = self.zones.get(zone_id)
        if not zone:
            raise TotalConnectError(f"zone {zone_id} does not exist")
        return zone.status

    def arm_custom(self, arm_type: ArmType) -> Dict[str, Any]:
        """NOT OPERATIONAL YET."""
        raise TotalConnectError("arm_custom is not operational yet")

    def get_custom_arm_settings(self) -> Dict[str, Any]:
        """NOT OPERATIONAL YET."""
        raise TotalConnectError("get_custom_arm_settings is not operational yet")

    def _update_zone_details(self, result: Dict[str, Any]) -> None:
        """
        Update from ZoneStatusListEx_V1.

        ZoneStatusInfoWithPartitionId provides additional info for setting up zones.
        If we used TotalConnectZone._update() it would overwrite missing data with None.
        """
        zone_info = result["ZoneStatus"]["Zones"]
        if not zone_info:
            LOGGER.warning(
                "No zones found when starting TotalConnect. Try to sync your panel using the TotalConnect app or website."
            )
            LOGGER.debug(f"_update_zone_details result: {result}")
        else:
            for zonedata in zone_info:
                self.zones[zonedata["ZoneID"]] = TotalConnectZone(zonedata, self)

    def _update_status(self, result: Dict[str, Any]) -> None:
        """Update from result."""
        data = (result or {}).get("PanelStatus")
        if not data:
            raise PartialResponseError("no PanelStatus", result)

        self.ac_loss = data.get("IsInACLoss")
        self.low_battery = data.get("IsInLowBattery")
        self.cover_tampered = data.get("IsCoverTampered")
        self.last_updated_timestamp_ticks = data.get("LastUpdatedTimestampTicks")
        self.configuration_sequence_number = data.get("ConfigurationSequenceNumber")

        # TODO: new resposne structure has a lot more data than we use here
        # and some fields are provided twice...are we using the right tones?

        astate = result.get("ArmingState")
        if not astate:
            raise PartialResponseError("no ArmingState", result)
        try:
            self.arming_state = ArmingState(astate)
        except ValueError:
            LOGGER.error(
                f"unknown location ArmingState {astate} in {result}: please report at {PROJECT_URL}/issues"
            )
            raise TotalConnectError(
                f"unknown location ArmingState {astate} in {result}"
            ) from None

    def _update_partitions(self, partitions: Dict[str, Any]) -> None:
        """Update partition info from Partitions."""
        # loop through partitions and update
        # NOTE: do not use keys because they don't line up with PartitionID
        for partition in partitions:
            if "PartitionID" not in partition:
                raise PartialResponseError("no PartitionID", partitions)
            partition_id = partition["PartitionID"]
            if partition_id in self.partitions:
                self.partitions[partition_id]._update(partition)
            else:
                LOGGER.warning(f"Update provided for unknown partion {partition_id}")

    def _update_zones(self, zones: Dict[str, Any]) -> None:
        """Update zone info from Zones."""
        if not zones:
            LOGGER.error(
                "no zones found: sync your panel using TotalConnect app or website"
            )
            raise TotalConnectError("no zones found: panel sync required")

        for zonedata in zones:
            zone_id = zonedata["ZoneID"]
            zone = self.zones.get(zone_id)
            if zone:
                zone._update(zonedata)
            else:
                zone = TotalConnectZone(zonedata, self)
                self.zones[zone_id] = zone

            if (
                zone.is_low_battery()
                and zone.can_be_bypassed
                and self.auto_bypass_low_battery
            ):
                self.zone_bypass(zone_id)

    def sync_panel(self) -> None:
        """Syncronize the panel with the TotalConnect server."""
        result = self.parent.http_request(
            endpoint=make_http_endpoint(
                f"api/v1/locations/{self.location_id}/devices/security/synchronize"
            ),
            method="POST",
            data={"userCode": self.usercode},
        )
        self.parent.raise_for_resultcode(result)
        self._sync_job_id = result.get("JobID")
        # Successful request so assume state is in progress
        LOGGER.info(f"Started sync of panel for location {self.location_id}")

    def get_cameras(self) -> None:
        """Get cameras for the location."""
        result = self.parent.http_request(
            endpoint=make_http_endpoint(
                f"api/v1/locations/{self.location_id}/GetLocationAllCameraListEx"
            ),
            method="GET",
        )
        self.parent.raise_for_resultcode(result)

        if "AccountAllCameraList" not in result:
            LOGGER.info(f"No cameras found for location {self.location_id}")
            return

        camera_list = result["AccountAllCameraList"]

        if "WiFiDoorbellList" in camera_list:
            self._get_doorbell(camera_list["WiFiDoorbellList"])

        if "UnicornList" in camera_list:
            self._get_unicorn(camera_list["UnicornList"])

        if "VideoPirList" in camera_list:
            self._get_video(camera_list["VideoPirList"])

        # TODO: look at Gen5DoorbellList and DoorBellList and lots of other info available

    def _get_doorbell(self, data: Dict[str, Any]) -> None:
        """Find doorbell info."""
        if not data or "WiFiDoorbellsList" not in data:
            return

        doorbells = data["WiFiDoorbellsList"]
        if "WiFiDoorBellInfo" not in doorbells:
            return

        doorbell_list = doorbells["WiFiDoorBellInfo"]
        for doorbell in doorbell_list:
            id = doorbell["DeviceID"]
            if id in self.devices:
                self.devices[id].doorbell_info = doorbell

    def _get_unicorn(self, data: Dict[str, Any]) -> None:
        """Find uniforn info."""
        if not data or "UnicornList" not in data:
            return

        unicorns = data["UnicornsList"]
        if "UnicornInfo" not in unicorns:
            return

        unicorn_list = unicorns["UnicornInfo"]
        for unicorn in unicorn_list:
            id = unicorn["DeviceID"]
            if id in self.devices:
                self.devices[id].unicorn_info = unicorn

    def _get_video(self, data: Dict[str, Any]) -> None:
        """Get video for the location."""
        if not data or "VideoPirInfo" not in data:
            return

        info = data["VideoPirInfo"]

        for video in info:
            id = video["DeviceID"]
            if id in self.devices:
                self.devices[id].video_info = video
