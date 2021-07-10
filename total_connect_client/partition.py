"""Total Connect Partition."""


class TotalConnectPartition:
    """Partition class for Total Connect."""

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
        """Update partition based on PartitionInfo. True on success."""
        if info is None:
            return False

        if "ArmingState" not in info:
            return False

        self.arming_state = info["ArmingState"]
        return True

    def arm_away(self):
        """Arm the partition (Away). True on success."""
        return self.parent.arm_away(self.id)

    def arm_stay(self):
        """Arm the partition (Stay). True on success."""
        return self.parent.arm_stay(self.id)

    def arm_stay_instant(self):
        """Arm the partition (Stay - Instant). True on success."""
        return self.parent.arm_stay_instant(self.id)

    def arm_away_instant(self):
        """Arm the partition (Away - Instant). True on success."""
        return self.parent.arm_away_instant(self.id)

    def arm_stay_night(self):
        """Arm the partition (Stay - Night). True on success."""
        return self.parent.arm_stay_night(self.id)

    def disarm(self):
        """Disarm the partition. True on success."""
        return self.parent.disarm(self.id)
