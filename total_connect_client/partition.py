"""Total Connect Partition."""

import logging

from .const import ArmingState
from .exceptions import PartialResponseError


LOGGER = logging.getLogger(__name__)


class TotalConnectPartition:
    """Partition class for Total Connect."""

    def __init__(self, details, parent):
        """Initialize Partition based on PartitionDetails."""
        self.parent = parent
        self.id = details.get("PartitionID")
        self.name = details.get("PartitionName")
        self.update(details)

    def __str__(self):
        """Return a string that is printable."""
        data = f"PARTITION {self.id} - {self.name}\n" f"  {self.arming_state}\n"
        return data

    def update(self, info):
        """Update partition based on PartitionInfo."""
        astate = (info or {}).get("ArmingState")
        if astate is None:
            raise PartialResponseError("no ArmingState")
        try:
            self.arming_state = ArmingState(astate)
        except ValueError:
            LOGGER.error(f"unknown ArmingState {astate} in {result} -- please file an issue at https://github.com/craigjmidwinter/total-connect-client/issues")
            raise

    def arm(self, arm_type):
        """Arm the partition."""
        self.parent.arm(arm_type, self.id)

    def disarm(self):
        """Disarm the partition."""
        self.parent.disarm(self.id)
