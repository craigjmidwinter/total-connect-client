"""Total Connect Partition."""

from .exceptions import PartialResponseError

class TotalConnectPartition:
    """Partition class for Total Connect."""


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

    def __init__(self, details, parent):
        """Initialize Partition based on PartitionDetails."""
        self.id = details.get("PartitionID")
        self.arming_state = details.get("ArmingState")
        self.name = details.get("PartitionName")
        self.parent = parent

    def __str__(self):
        """Return a string that is printable."""
        data = (
            f"PARTITION {self.id} - {self.name}\n"
            f"  ArmingState: {self.arming_state}\n"
        )

        return data

    def update(self, info):
        """Update partition based on PartitionInfo."""
        astate = (info or {}).get("ArmingState")
        if astate is None:
            raise PartialResponseError('no ArmingState')
        self.arming_state = astate

    def arm_away(self):
        """Arm the partition (Away)."""
        self.parent.arm_away(self.id)

    def arm_stay(self):
        """Arm the partition (Stay)."""
        self.parent.arm_stay(self.id)

    def arm_stay_instant(self):
        """Arm the partition (Stay - Instant). True on success."""
        self.parent.arm_stay_instant(self.id)

    def arm_away_instant(self):
        """Arm the partition (Away - Instant)."""
        self.parent.arm_away_instant(self.id)

    def arm_stay_night(self):
        """Arm the partition (Stay - Night)."""
        self.parent.arm_stay_night(self.id)

    def disarm(self):
        """Disarm the partition."""
        self.parent.disarm(self.id)

    def get_armed_status(self):
        """Get the status of the panel."""
        # TODO:  ask parent to update status first?
        return self.arming_state

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
