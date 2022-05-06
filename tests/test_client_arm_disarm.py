"""Test total_connect_client."""

import unittest
from unittest.mock import patch

import pytest
from common import create_client
from const import (
    LOCATION_INFO_BASIC_NORMAL,
    RESPONSE_ARMED_AWAY,
    RESPONSE_ARMED_STAY,
    RESPONSE_ARMED_STAY_NIGHT,
    RESPONSE_DISARMED,
)

from total_connect_client import ArmingHelper
from total_connect_client.const import ArmingState, _ResultCode
from total_connect_client.exceptions import BadResultCodeError, UsercodeInvalid, UsercodeUnavailable

TCC_REQUEST_METHOD = "total_connect_client.client.TotalConnectClient.request"

RESPONSE_ARM_SUCCESS = {
    "ResultCode": _ResultCode.ARM_SUCCESS.value,
    "ResultData": "testing arm success",
}
RESPONSE_DISARM_SUCCESS = {
    "ResultCode": _ResultCode.DISARM_SUCCESS.value,
    "ResultData": "testing disarm success",
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


class TestTotalConnectClient(unittest.TestCase):
    """Test TotalConnectClient."""

    def setUp(self):
        """Test setup."""
        self.location_id = LOCATION_INFO_BASIC_NORMAL["LocationID"]

    def tests_arm(self):
        def run(error, responses, armit, armingstate):
            client = create_client()
            location = client.locations[self.location_id]
            with patch(TCC_REQUEST_METHOD, side_effect=responses):
                if error:
                    with pytest.raises(error):
                        armit(location)
                else:
                    armit(location)
                location.get_panel_meta_data()
                assert location.arming_state == armingstate

        def runall(success_response, armit, success_armingstate):
            # first test is all good
            run(
                None,
                [RESPONSE_ARM_SUCCESS, success_response],
                armit,
                success_armingstate,
            )
            for failresponse in (
                RESPONSE_ARM_FAILED,  # "zone faulted"
            ):
                run(
                    BadResultCodeError,
                    [failresponse, RESPONSE_DISARMED],
                    armit,
                    ArmingState.DISARMED,
                )
            # last test has 'unavailable' usercode
            run(
                UsercodeUnavailable,
                [RESPONSE_USER_CODE_UNAVAILABLE, RESPONSE_DISARMED],
                armit,
                ArmingState.DISARMED,
            )

        runall(
            RESPONSE_ARMED_AWAY,
            lambda loc: ArmingHelper(loc).arm_away(),
            ArmingState.ARMED_AWAY,
        )
        # this test claims to be testing arm away instant but uses the
        # arm away response
        runall(
            RESPONSE_ARMED_AWAY,
            lambda loc: ArmingHelper(loc).arm_away_instant(),
            ArmingState.ARMED_AWAY,
        )
        runall(
            RESPONSE_ARMED_STAY,
            lambda loc: ArmingHelper(loc).arm_stay(),
            ArmingState.ARMED_STAY,
        )
        # this test claims to be testing arm stay instant but uses the
        # arm stay response
        runall(
            RESPONSE_ARMED_STAY,
            lambda loc: ArmingHelper(loc).arm_stay_instant(),
            ArmingState.ARMED_STAY,
        )
        runall(
            RESPONSE_ARMED_STAY_NIGHT,
            lambda loc: ArmingHelper(loc).arm_stay_night(),
            ArmingState.ARMED_STAY_NIGHT,
        )

    def tests_disarm(self):
        """Test disarm."""
        # first test with no issues
        client = create_client()
        location = client.locations[self.location_id]
        responses = [
            RESPONSE_ARM_SUCCESS,
            RESPONSE_ARMED_AWAY,
            RESPONSE_DISARM_SUCCESS,
            RESPONSE_DISARMED,
        ]
        with patch(TCC_REQUEST_METHOD, side_effect=responses):
            # arm the system and confirm armed_away
            ArmingHelper(location).arm_away()
            location.get_panel_meta_data()
            assert location.arming_state.is_armed_away()

            # now disarm
            ArmingHelper(location).disarm()
            location.get_panel_meta_data()
            assert location.arming_state.is_disarmed()

    def tests_disarm_command_failed(self):
        """Test disarm with command failed."""
        # first test with no issues
        client = create_client()
        location = client.locations[self.location_id]
        responses = [
            RESPONSE_ARM_SUCCESS,
            RESPONSE_ARMED_AWAY,
            RESPONSE_DISARM_FAILED,
            RESPONSE_ARMED_AWAY,
        ]
        with patch(TCC_REQUEST_METHOD, side_effect=responses):
            # arm the system and confirm armed_away
            ArmingHelper(location).arm_away()
            location.get_panel_meta_data()
            assert location.arming_state.is_armed_away()

            # now disarm, should fail
            with pytest.raises(BadResultCodeError):
                ArmingHelper(location).disarm()

            # should still be armed_away
            location.get_panel_meta_data()
            assert location.arming_state.is_armed_away()

    def tests_disarm_user_code_invalid(self):
        """Test disarm with invalid user code."""
        client = create_client()
        location = client.locations[self.location_id]
        responses = [
            RESPONSE_ARM_SUCCESS,
            RESPONSE_ARMED_AWAY,
            RESPONSE_USER_CODE_INVALID,
            RESPONSE_ARMED_AWAY,
        ]
        with patch(TCC_REQUEST_METHOD, side_effect=responses):
            # arm the system and confirm armed_away
            ArmingHelper(location).arm_away()
            location.get_panel_meta_data()
            assert location.arming_state.is_armed_away()

            with pytest.raises(UsercodeInvalid):
                ArmingHelper(location).disarm()

            # should still be armed_away when disarming fails
            location.get_panel_meta_data()
            assert location.arming_state.is_armed_away()

    def tests_disarm_disarmed(self):
        """Test attempt to disarm an already disarmed system."""
        # Did this once on my Lynx 7000 and it gave result code SUCCESS

        client = create_client()
        location = client.locations[self.location_id]
        responses = [RESPONSE_DISARMED, RESPONSE_SUCCESS, RESPONSE_DISARMED]
        with patch(TCC_REQUEST_METHOD, side_effect=responses):
            location.get_panel_meta_data()
            assert location.arming_state.is_disarmed()

            # now disarm
            ArmingHelper(location).disarm()
            location.get_panel_meta_data()
            assert location.arming_state.is_disarmed()
