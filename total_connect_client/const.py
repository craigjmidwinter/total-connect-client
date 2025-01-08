"""Total Connect Client constants."""

from enum import Enum
from typing import Dict, Any

from .exceptions import BadResultCodeError, ServiceUnavailable


class ArmType(Enum):
    """Represent ArmingType."""

    AWAY = 0
    STAY = 1
    STAY_INSTANT = 2
    AWAY_INSTANT = 3
    STAY_NIGHT = 4


class ArmingState(Enum):
    """Represent ArmingState."""

    DISARMED = 10200
    DISARMED_BYPASS = 10211
    DISARMED_ZONE_FAULTED = (
        10214  # seems to apply to location, not to partition.  See issue #144
    )

    ARMED_AWAY = 10201
    ARMED_AWAY_BYPASS = 10202
    ARMED_STAY = 10203
    ARMED_STAY_OTHER = 10226
    ARMED_STAY_PROA7 = 10230  # issue #173
    ARMED_STAY_BYPASS_PROA7 = 10231  # issue #177
    ARMED_STAY_INSTANT_PROA7 = 10232  # issue #177
    ARMED_STAY_INSTANT_BYPASS_PROA7 = 10233  # issue #177
    ARMED_STAY_BYPASS = 10204
    ARMED_AWAY_INSTANT = 10205
    ARMED_AWAY_INSTANT_BYPASS = 10206
    ARMED_STAY_INSTANT = 10209
    ARMED_STAY_INSTANT_BYPASS = 10210
    ARMED_STAY_NIGHT = 10218
    ARMED_STAY_NIGHT_BYPASS_PROA7 = 10219  # issue #177
    ARMED_STAY_NIGHT_INSTANT_PROA7 = 10220  # issue #177
    ARMED_STAY_NIGHT_INSTANT_BYPASS_PROA7 = 10221  # issue #177
    ARMED_CUSTOM_BYPASS = 10223

    ALARMING = 10207
    ALARMING_FIRE_SMOKE = 10212
    ALARMING_CARBON_MONOXIDE = 10213
    ALARMING_CARBON_MONOXIDE_PROA7 = 10215

    ARMING = 10307
    DISARMING = 10308

    UNKNOWN = 0

    def is_arming(self) -> bool:
        """Return true if the system is in the process of arming."""
        return self == ArmingState.ARMING

    def is_disarming(self) -> bool:
        """Return true if the system is in the process of disarming."""
        return self == ArmingState.DISARMING

    def is_pending(self) -> bool:
        """Return true if the system is pending an action."""
        return self.is_disarming() or self.is_arming()

    def is_disarmed(self) -> bool:
        """Return True if the system is disarmed."""
        return self in (
            ArmingState.DISARMED,
            ArmingState.DISARMED_BYPASS,
            ArmingState.DISARMED_ZONE_FAULTED,
        )

    def is_armed_away(self) -> bool:
        """Return True if the system is armed away in any way."""
        return self in (
            ArmingState.ARMED_AWAY,
            ArmingState.ARMED_AWAY_BYPASS,
            ArmingState.ARMED_AWAY_INSTANT,
            ArmingState.ARMED_AWAY_INSTANT_BYPASS,
        )

    def is_armed_custom_bypass(self) -> bool:
        """Return True if the system is armed custom bypass in any way."""
        return self == ArmingState.ARMED_CUSTOM_BYPASS

    def is_armed_home(self) -> bool:
        """Return True if the system is armed home/stay in any way."""
        return self in (
            ArmingState.ARMED_STAY,
            ArmingState.ARMED_STAY_PROA7,
            ArmingState.ARMED_STAY_BYPASS,
            ArmingState.ARMED_STAY_BYPASS_PROA7,
            ArmingState.ARMED_STAY_INSTANT,
            ArmingState.ARMED_STAY_INSTANT_PROA7,
            ArmingState.ARMED_STAY_INSTANT_BYPASS,
            ArmingState.ARMED_STAY_INSTANT_BYPASS_PROA7,
            ArmingState.ARMED_STAY_NIGHT,
            ArmingState.ARMED_STAY_NIGHT_BYPASS_PROA7,
            ArmingState.ARMED_STAY_NIGHT_INSTANT_PROA7,
            ArmingState.ARMED_STAY_NIGHT_INSTANT_BYPASS_PROA7,
            ArmingState.ARMED_STAY_OTHER,
        )

    def is_armed_night(self) -> bool:
        """Return True if the system is armed night in any way."""
        return self in (
            ArmingState.ARMED_STAY_NIGHT,
            ArmingState.ARMED_STAY_NIGHT_BYPASS_PROA7,
            ArmingState.ARMED_STAY_NIGHT_INSTANT_PROA7,
            ArmingState.ARMED_STAY_NIGHT_INSTANT_BYPASS_PROA7,
        )

    def is_armed(self) -> bool:
        """Return True if the system is armed in any way."""
        return (
            self.is_armed_away()
            or self.is_armed_home()
            or self.is_armed_night()  # noqa: W504
            or self.is_armed_custom_bypass()
        )

    def is_triggered_police(self) -> bool:
        """Return True if the system is triggered for police or medical."""
        return self == ArmingState.ALARMING

    def is_triggered_fire(self) -> bool:
        """Return True if the system is triggered for fire or smoke."""
        return self == ArmingState.ALARMING_FIRE_SMOKE

    def is_triggered_gas(self) -> bool:
        """Return True if the system is triggered for carbon monoxide."""
        return self in (
            ArmingState.ALARMING_CARBON_MONOXIDE,
            ArmingState.ALARMING_CARBON_MONOXIDE_PROA7,
        )

    def is_triggered(self) -> bool:
        """Return True if the system is triggered in any way."""
        return (
            self.is_triggered_fire()
            or self.is_triggered_gas()
            or self.is_triggered_police()
        )


class _ResultCode(Enum):
    """Represent ResultCode.

    As suggested by the leading underscore, this class is not used by
    callers of the API.
    """

    @staticmethod
    def from_response(response_dict:Dict[str, Any]):
        try:
            return _ResultCode(response_dict["ResultCode"])
        except TypeError:
            # sometimes when there are server issues,
            # it returns empty responses - see issue #228
            raise ServiceUnavailable(
                f"Server returned empty response, check server status at {STATUS_URL}"
            ) from None
        except ValueError:
            raise BadResultCodeError(
                f"unknown result code {response_dict['ResultCode']}", response_dict
            ) from None

    SUCCESS = 0
    ARM_SUCCESS = 4500
    DISARM_SUCCESS = 4500
    SESSION_INITIATED = 4500

    BAD_USER_OR_PASSWORD = -50004
    INVALID_SESSIONID = -30002
    FAILED_TO_BYPASS_ZONE = -4504
    COMMAND_FAILED = -4502
    USER_CODE_UNAVAILABLE = -4114
    USER_CODE_INVALID = -4106
    FAILED_TO_CONNECT = -4104

    # Invalid Parameter returned when requesting SyncPanelStatus
    # using non-existant JobID.
    INVALID_PARAMETER = -501

    BAD_OBJECT_REFERENCE = -400
    FEATURE_NOT_SUPPORTED = -120
    INVALID_SESSION = -102
    AUTHENTICATION_FAILED = -100
    CONNECTION_ERROR = 4101
    ACCOUNT_LOCKED = -123


PROJECT_URL = "https://github.com/craigjmidwinter/total-connect-client"

STATUS_URL = "https://status.resideo.com/"
