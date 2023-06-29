"""Test total_connect_client."""

from unittest.mock import patch

from common import create_client
from const import (
    LOCATION_INFO_BASIC_NORMAL,
    RESPONSE_ARMED_AWAY,
    TCC_REQUEST_METHOD,
    # these are tested in test_client_arm_disarm for now
    # RESPONSE_ARMED_STAY,
    # RESPONSE_ARMED_STAY_NIGHT,
    # RESPONSE_DISARMED,
    # RESPONSE_FEATURE_NOT_SUPPORTED,
)

from total_connect_client.const import _ResultCode
from total_connect_client.client import ArmingHelper

# from total_connect_client.exceptions import AuthenticationError, BadResultCodeError


RESPONSE_ARM_SUCCESS = {
    "ResultCode": _ResultCode.ARM_SUCCESS.value,
    "ResultData": "testing arm success",
}

# returned when a zone is faulted
RESPONSE_ARM_FAILED = {
    "ResultCode": _ResultCode.COMMAND_FAILED.value,
    "ResultData": "testing arm failed",
}
RESPONSE_DISARM_FAILED = {
    "ResultCode": _ResultCode.COMMAND_FAILED.value,
    "ResultData": "testing disarm failed",
}

# appears to be for a bad/wrong code
RESPONSE_USER_CODE_INVALID = {
    "ResultCode": _ResultCode.USER_CODE_INVALID.value,
    "ResultData": "testing user code invalid",
}

# appears to be for a code entered for a wrong device/location
RESPONSE_USER_CODE_UNAVAILABLE = {
    "ResultCode": _ResultCode.USER_CODE_UNAVAILABLE.value,
    "ResultData": "testing user code unavailable",
}

RESPONSE_SUCCESS = {
    "ResultCode": _ResultCode.SUCCESS.value,
    "ResultData": "testing success",
}


def tests_arm_away():
    """Test arm away."""
    # first test with no issues
    client = create_client()
    location = client.locations[LOCATION_INFO_BASIC_NORMAL["LocationID"]]

    responses = [RESPONSE_ARM_SUCCESS, RESPONSE_ARMED_AWAY]
    with patch(TCC_REQUEST_METHOD, side_effect=responses):
        ArmingHelper(location).arm_away()

        # confirm armed_away
        location.get_panel_meta_data()
        assert location.arming_state.is_armed_away()
        assert location.partitions[1].arming_state.is_armed_away()
