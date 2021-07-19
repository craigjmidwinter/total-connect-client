"""Total Connect Partition."""


ARM_TYPE_AWAY = 0
ARM_TYPE_STAY = 1
ARM_TYPE_STAY_INSTANT = 2
ARM_TYPE_AWAY_INSTANT = 3
ARM_TYPE_STAY_NIGHT = 4

class Armable:
    """Partitions and Locations are both Armable.

    Users of TotalConnectClient never instantiate Armables.
    """
    # This is an abstract base class. Subclasses must define a method
    #    _armer_disarmer(self, arm_type, partition_id)
    # that actually performs the requested arming/disarming.

    # values for ArmingState

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

    def __init__(self, id=None):
        self.id = id
        self.arming_state = None

    def __str__(self):
        ident = f"  ID: {self.id}\n" if self.id else ""
        return f"  ArmingState: {self.arming_state}\n{ident}"

    def set_arming_state(self, new_state):
        """Set arming state.  True on success."""
        if new_state is None:
            return False
        self.arming_state = new_state
        return True

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

    def arm_away(self):
        """Arm the system (Away)."""
        return self.arm(ARM_TYPE_AWAY)

    def arm_stay(self):
        """Arm the system (Stay)."""
        return self.arm(ARM_TYPE_STAY)

    def arm_stay_instant(self):
        """Arm the system (Stay - Instant)."""
        return self.arm(ARM_TYPE_STAY_INSTANT)

    def arm_away_instant(self):
        """Arm the system (Away - Instant)."""
        return self.arm(ARM_TYPE_AWAY_INSTANT)

    def arm_stay_night(self):
        """Arm the system (Stay - Night)."""
        return self.arm(ARM_TYPE_STAY_NIGHT)

    def arm(self, arm_type):
        """Arm partition self.id, or arm all partitions if self.id is None.
        Return True if successful.
        """
        return self._armer_disarmer(arm_type, self.id)

    def disarm(self):
        """Disarm partition self.id, or disarm all partitions if self.id is None.
        Return True if successful.
        """
        return self._armer_disarmer(None, self.id)


class TotalConnectPartition(Armable):
    """Partition class for Total Connect. To arm or disarm this partition,
    call the methods from Armable.
    """
    def __init__(self, details, parent):
        """Initialize Partition based on PartitionDetails."""
        super().__init__(details.get("PartitionID"))
        self.set_arming_state(details.get("ArmingState"))
        self.name = details.get("PartitionName")
        self.parent = parent

    def __str__(self):
        return f"PARTITION {self.id} - {self.name}\n{super().__str__()}"

    def update(self, info):
        """Update partition based on PartitionInfo. True on success."""
        return self.set_arming_state((info or {}).get("ArmingState"))

    def get_armed_status(self):
        """Get the status of the panel."""
        # TODO:  ask parent to update status first?
        return self.arming_state

    def _armer_disarmer(self, arm_type, partition_id):
        return self.parent._armer_disarmer(arm_type, partition_id)
