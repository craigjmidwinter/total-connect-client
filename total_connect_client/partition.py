"""Total Connect Partition."""


class TotalConnectPartition:
    """Partition class for Total Connect."""

    def __init__(self, details):
        """Initialize Partition based on PartitionDetails."""
        self.id = details.get("PartitionID")
        self.arming_state = details.get("ArmingState")
        self.name = details.get("PartitionName")

    def __str__(self):
        """Return a string that is printable."""
        data = (
            f"PARTITION {self.id} - {self.name}\n"
            f"  ArmingState: {self.arming_state}\n"
        )

        return data

    def update(self, info):
        """Update partition based on PartitionInfo."""
        if info is None:
            return False

        if "ArmingState" not in info:
            return False

        self.arming_state = info["ArmingState"]
        return True
