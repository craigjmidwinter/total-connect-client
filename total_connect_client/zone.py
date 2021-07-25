"""Total Connect Zone."""


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
        self.partition = zone.get("PartitionID")
        self.status = zone.get("ZoneStatus")
        self.can_be_bypassed = zone.get("CanBeBypassed")

        self.zone_type_id = zone.get("ZoneTypeId", self.zone_type_id)
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
        return self.status & ZONE_STATUS_BYPASSED > 0

    def _mark_as_bypassed(self):
        """Set is_bypassed status."""
        # TODO: when does this get reset to no longer bypassed?
        self.status |= ZONE_STATUS_BYPASSED

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
        # FIXME: should this be self.is_type_security() instead?
        if self.zone_type_id == ZONE_TYPE_SECURITY and not self.can_be_bypassed:
            return True

        if self.zone_type_id in (ZONE_TYPE_PROA7_MEDICAL, ZONE_TYPE_PROA7_POLICE):
            return True

        return False

    def is_type_security(self):
        """Return true if zone type is security."""

        # LYRIC_POLICE is here but PROA7_POLICE is not. why?
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
