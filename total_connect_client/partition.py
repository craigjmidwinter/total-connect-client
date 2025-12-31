"""Total Connect Partition."""

import logging
from typing import Any, Final, TYPE_CHECKING

from .const import PROJECT_URL, ArmingState, ArmType
from .exceptions import PartialResponseError, TotalConnectError

if TYPE_CHECKING:
    from .location import TotalConnectLocation

LOGGER: Final = logging.getLogger(__name__)


class TotalConnectPartition:
    """Partition class for Total Connect."""

    def __init__(self, details: dict[str, Any], parent: "TotalConnectLocation"):
        """Initialize Partition based on PartitionDetails."""
        self.parent: "TotalConnectLocation" = parent
        self.partitionid: int | None = details.get("PartitionID")
        self.name: str | None = details.get("PartitionName")
        self.is_stay_armed: bool | None = details.get("IsStayArmed")
        self.is_fire_enabled: bool | None = details.get("IsFireEnabled")
        self.is_common_enabled: bool | None = details.get("IsCommonEnabled")
        self.is_locked: bool | None = details.get("IsLocked")
        self.is_new_partition: bool | None = details.get("IsNewPartition")
        self.is_night_stay_enabled: bool | None = details.get("IsNightStayEnabled")
        self.exit_delay_timer: int | None = details.get("ExitDelayTimer")
        self.arming_state: ArmingState  # Set by _update()
        self._update(details)

    def __str__(self) -> str:  # pragma: no cover
        """Return a string that is printable."""
        data = (
            f"PARTITION {self.partitionid} - {self.name}\n"
            f"  {self.arming_state}\n"
            f"  Stay armed: {self.is_stay_armed}\tFire enabled: {self.is_fire_enabled}\n"
            f"  Common enabled: {self.is_common_enabled}\tLocked: {self.is_locked}\n"
            f"  New: {self.is_new_partition}\tNight Stay enabled: {self.is_night_stay_enabled}\n"
            f"  Exit delay: {self.exit_delay_timer}\n"
        )

        return data

    def arm(self, arm_type: ArmType, usercode: str = "") -> None:
        """Arm the partition."""
        self.parent.arm(arm_type, self.partitionid, usercode)

    def disarm(self, usercode: str = "") -> None:
        """Disarm the partition."""
        self.parent.disarm(self.partitionid, usercode)

    def _update(self, info: dict[str, Any]) -> None:
        """Update partition state from PartitionInfo data.
        
        Args:
            info: Dictionary containing partition information from API
            
        Raises:
            PartialResponseError: If ArmingState is missing from info
            TotalConnectError: If ArmingState value is unknown
        """
        astate = (info or {}).get("ArmingState")
        if astate is None:
            raise PartialResponseError("no ArmingState")
        try:
            self.arming_state = ArmingState(astate)
        except ValueError:
            LOGGER.error(
                f"unknown partition ArmingState {astate} in {info}: report at {PROJECT_URL}/issues"
            )
            raise TotalConnectError(
                f"unknown partition ArmingState {astate} in {info}"
            ) from None
