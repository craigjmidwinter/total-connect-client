"""Total Connect Partition."""

import logging

from .const import ArmingState, PROJECT_URL
from .exceptions import PartialResponseError, TotalConnectError


LOGGER = logging.getLogger(__name__)


class TotalConnectPartition:
    """Partition class for Total Connect."""

    def __init__(self, details, parent):
        """Initialize Partition based on PartitionDetails."""
        self.parent = parent
        self.partitionid = details.get("PartitionID")
        self.name = details.get("PartitionName")
        self._update(details)

    def __str__(self):
        """Return a string that is printable."""
        data = f"PARTITION {self.partitionid} - {self.name}\n" f"  {self.arming_state}\n"
        return data

    def arm(self, arm_type):
        """Arm the partition."""
        self.parent.arm(arm_type, self.partitionid)

    def disarm(self):
        """Disarm the partition."""
        self.parent.disarm(self.partitionid)

    def _update(self, info):
        """Update partition based on PartitionInfo."""
        astate = (info or {}).get("ArmingState")
        if astate is None:
            raise PartialResponseError("no ArmingState")
        try:
            self.arming_state = ArmingState(astate)
        except ValueError:
            LOGGER.error(f"unknown ArmingState {astate} in {info}: report at {PROJECT_URL}/issues")
            raise TotalConnectError(f"unknown ArmingState {astate} in {info}") from None
