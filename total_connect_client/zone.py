"""Total Connect Zone."""

import logging
from enum import Enum, IntFlag


LOGGER = logging.getLogger(__name__)


class ZoneStatus(IntFlag):
    NORMAL      =   0
    BYPASSED    =   1
    FAULT       =   2
    TROUBLE     =   8  # is also Tampered
    LOW_BATTERY =  64
    TRIGGERED   = 256


class ZoneType(Enum):
    """
    These are the "standard" Honeywell zone types. However some panels such
    as the Lynx 7000 report most security zones as zone type 3.

    https://www.alarmliquidators.com/content/Vista%2021IP-%20Programming%20Guide.pdf
    http://techresource.online/training/ssnw/honeywell/zone-types
    """
    SECURITY          = 0  # for Vista, zone type 0 is not used
    ENTRY_EXIT1       = 1  # starts countdown timer #1
    ENTRY_EXIT2       = 2  # like ENTRY_EXIT1 but uses timer #2
    PERIMETER         = 3  # zone type 3 usually triggers an immediate alarm...
    PROA7_SECURITY    = 3  # but some panels like Lynx 7000 report timed zones as 3
    INTERIOR_FOLLOWER = 4  # inactive when armed STAY
    TROUBLE_ALARM     = 5  # trouble by day, alarm by night
    SILENT_24HR       = 6  # 24-hour silent alarm (often used for police/hold-up)
    AUDIBLE_24HR      = 7  # 24-hour audible alarm (often used for police)
    AUX_24HR          = 8  # no local siren but keypad beeps (often used for medical)
    FIRE_SMOKE        = 9
    INTERIOR_DELAY    = 10 # inactive when armed STAY, otherwise like ENTRY_EXIT1
    MONITOR           = 12  # e.g. temperature or flood
    CARBON_MONOXIDE   = 14
    PROA7_MEDICAL     = 15
    FIRE_W_VERIFICATION = 16  # must trigger twice to cause an alarm
    LYRIC_LOCAL_ALARM = 89

    # According to the VISTA docs, these can be programmed via downloader software
    # or from a keypad using data fields *182-*185

    VISTA_CONFIGURABLE_90 = 90
    VISTA_CONFIGURABLE_91 = 91
    VISTA_CONFIGURABLE_92 = 92
    VISTA_CONFIGURABLE_93 = 93


class TotalConnectZone:
    """Do not create instances of this class yourself."""

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
        """Update the zone."""
        assert zone
        zid = zone.get("ZoneID")
        assert self.id == zid, (self.id, zid)

        self.description = zone.get("ZoneDescription")
        # ZoneInfo gives 'PartitionID' but ZoneStatusInfoWithPartitionId gives 'PartitionId'
        if "PartitionId" in zone:
            # ...and PartitionId gives an int instead of a string
            self.partition = str(zone["PartitionId"])
        else:
            self.partition = zone.get("PartitionID")
        try:
            self.status = ZoneStatus(zone.get("ZoneStatus"))
        except ValueError:
            LOGGER.error(f"unknown ZoneStatus in {zone} -- please file an issue at https://github.com/craigjmidwinter/total-connect-client/issues")
            raise
        self.can_be_bypassed = zone.get("CanBeBypassed")

        try:
            zid = zone.get("ZoneTypeId", self.zone_type_id)
            # TODO: if zid is None should we raise PartialResponseError?
            self.zone_type_id = None if zid is None else ZoneType(zid)
        except ValueError:
            LOGGER.error(f"unknown ZoneType {zid} in {zone} -- please file an issue at https://github.com/craigjmidwinter/total-connect-client/issues")
            # if we get an unknown ZoneType we do not raise an exception, because
            # we know there are more zone types than we have in our enum, and
            # having an unknown ZoneType doesn't keep us from doing our work
            self.zone_type_id = zid

        self.battery_level = zone.get("Batterylevel", self.battery_level)
        self.signal_strength = zone.get("Signalstrength", self.signal_strength)
        info = zone.get("zoneAdditionalInfo")
        if info:
            self.sensor_serial_number = info.get("SensorSerialNumber")
            self.loop_number = info.get("LoopNumber")
            self.response_type = info.get("ResponseType")
            self.alarm_report_state = info.get("AlarmReportState")
            self.supervision_type = info.get("ZoneSupervisionType")
            self.chime_state = info.get("ChimeState")
            self.device_type = info.get("DeviceType")

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
        return self.status & ZoneStatus.BYPASSED > 0

    def _mark_as_bypassed(self):
        """Set is_bypassed status."""
        # TODO: when does this get reset to no longer bypassed?
        self.status |= ZoneStatus.BYPASSED

    def is_faulted(self):
        """Return true if the zone is faulted."""
        return self.status & ZoneStatus.FAULT > 0

    def is_tampered(self):
        """Return true if zone is tampered."""
        return self.status & ZoneStatus.TROUBLE > 0

    def is_low_battery(self):
        """Return true if low battery."""
        return self.status & ZoneStatus.LOW_BATTERY > 0

    def is_troubled(self):
        """Return true if zone is troubled."""
        return self.status & ZoneStatus.TROUBLE > 0

    def is_triggered(self):
        """Return true if zone is triggered."""
        return self.status & ZoneStatus.TRIGGERED > 0

    def is_type_button(self):
        """Return true if zone is a button."""

        # as seen so far, any security zone that cannot be bypassed is a button on a panel
        if self.is_type_security() and not self.can_be_bypassed:
            return True

        if self.zone_type_id in (
                ZoneType.PROA7_MEDICAL,
                ZoneType.AUDIBLE_24HR,
                ZoneType.SILENT_24HR,
        ):
            return True

        return False

    def is_type_security(self):
        """Return true if zone type is security."""

        return self.zone_type_id in (
            ZoneType.SECURITY,
            ZoneType.ENTRY_EXIT1,
            ZoneType.ENTRY_EXIT2,
            ZoneType.PERIMETER,
            ZoneType.INTERIOR_FOLLOWER,
            ZoneType.TROUBLE_ALARM,
            ZoneType.SILENT_24HR,
            ZoneType.AUDIBLE_24HR,
            ZoneType.INTERIOR_DELAY,
            ZoneType.LYRIC_LOCAL_ALARM,
        )

    def is_type_motion(self):
        """Return true if zone type is motion."""
        return self.zone_type_id == ZoneType.INTERIOR_FOLLOWER

    def is_type_fire(self):
        """Return true if zone type is fire or smoke."""
        # TODO: why is ZoneType.MONITOR here? it's not a fire or smoke zone type
        return self.zone_type_id in (ZoneType.FIRE_SMOKE, ZoneType.MONITOR)

    def is_type_carbon_monoxide(self):
        """Return true if zone type is carbon monoxide."""
        return self.zone_type_id == ZoneType.CARBON_MONOXIDE

    def is_type_medical(self):
        """Return true if zone type is medical."""
        return self.zone_type_id == ZoneType.PROA7_MEDICAL
