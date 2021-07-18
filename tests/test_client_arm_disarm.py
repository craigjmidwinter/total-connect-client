"""Test total_connect_client."""

from unittest.mock import patch
import unittest
import pytest

import TotalConnectClient
from common import create_client
from const import (
    LOCATION_INFO_BASIC_NORMAL,
    RESPONSE_ARMED_AWAY,
    RESPONSE_ARMED_STAY,
    RESPONSE_ARMED_STAY_NIGHT,
    RESPONSE_DISARMED,
    RESPONSE_FEATURE_NOT_SUPPORTED,
)
from exceptions import BadResultCodeError, AuthenticationError

RESPONSE_ARM_SUCCESS = {
    "ResultCode": TotalConnectClient.TotalConnectClient.ARM_SUCCESS,
    "ResultData": "testing arm success",
}
RESPONSE_DISARM_SUCCESS = {
    "ResultCode": TotalConnectClient.TotalConnectClient.DISARM_SUCCESS,
    "ResultData": "testing disarm success",
}

# returned when a zone is faulted
RESPONSE_ARM_FAILED = {
    "ResultCode": TotalConnectClient.TotalConnectClient.COMMAND_FAILED,
    "ResultData": "testing arm failed",
}
RESPONSE_DISARM_FAILED = {
    "ResultCode": TotalConnectClient.TotalConnectClient.COMMAND_FAILED,
    "ResultData": "testing disarm failed",
}

# appears to be for a bad/wrong code
RESPONSE_USER_CODE_INVALID = {
    "ResultCode": TotalConnectClient.TotalConnectClient.USER_CODE_INVALID,
    "ResultData": "testing user code invalid",
}

# appears to be for a code entered for a wrong device/location
RESPONSE_USER_CODE_UNAVAILABLE = {
    "ResultCode": TotalConnectClient.TotalConnectClient.USER_CODE_UNAVAILABLE,
    "ResultData": "testing user code unavailable",
}

RESPONSE_SUCCESS = {
    "ResultCode": TotalConnectClient.TotalConnectClient.SUCCESS,
    "ResultData": "testing success",
}


class TestTotalConnectClient(unittest.TestCase):
    """Test TotalConnectClient."""

    def setUp(self):
        """Test setup."""
        self.client = None
        self.location_id = LOCATION_INFO_BASIC_NORMAL["LocationID"]

    def tearDown(self):
        """Test cleanup."""
        self.client = None

    def tests_arm_away(self):
        """Test arm away."""
        # first test with no issues
        self.client = create_client()
        responses = [RESPONSE_ARM_SUCCESS, RESPONSE_ARMED_AWAY]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            self.client.arm_away(self.location_id)

            # confirm armed_away
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_away() is True

        # second test with a zone faulted
        self.client = create_client()
        responses = [RESPONSE_ARM_FAILED, RESPONSE_DISARMED]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            with pytest.raises(BadResultCodeError):
                self.client.arm_away(self.location_id)

            # should still be disarmed
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_away() is False
            assert self.client.locations[self.location_id].is_disarmed() is True

        # third test with bad usercode
        self.client = create_client()
        responses = [RESPONSE_USER_CODE_INVALID, RESPONSE_DISARMED]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            with pytest.raises(BadResultCodeError):
                self.client.arm_away(self.location_id)

            # should still be disarmed
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_away() is False
            assert self.client.locations[self.location_id].is_disarmed() is True

        # fourth test with 'unavailable' usercode
        self.client = create_client()
        responses = [RESPONSE_USER_CODE_UNAVAILABLE, RESPONSE_DISARMED]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            with pytest.raises(AuthenticationError):
                self.client.arm_away(self.location_id)

            # should still be disarmed
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_away() is False
            assert self.client.locations[self.location_id].is_disarmed() is True

        # fifth test with 'other' usercode
        self.client = create_client()
        responses = [RESPONSE_FEATURE_NOT_SUPPORTED, RESPONSE_DISARMED]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            with pytest.raises(BadResultCodeError):
                self.client.arm_away(self.location_id)

            # should still be disarmed
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_away() is False
            assert self.client.locations[self.location_id].is_disarmed() is True

    def tests_arm_away_instant(self):
        """Test arm away instant."""
        # first test with no issues
        self.client = create_client()
        responses = [RESPONSE_ARM_SUCCESS, RESPONSE_ARMED_AWAY]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            self.client.arm_away_instant(self.location_id)

            # confirm armed_away
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_away() is True

        # second test with a zone faulted
        self.client = create_client()
        responses = [RESPONSE_ARM_FAILED, RESPONSE_DISARMED]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            with pytest.raises(BadResultCodeError):
                self.client.arm_away_instant(self.location_id)

            # should still be disarmed
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_away() is False
            assert self.client.locations[self.location_id].is_disarmed() is True

        # third test with bad usercode
        self.client = create_client()
        responses = [RESPONSE_USER_CODE_INVALID, RESPONSE_DISARMED]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            with pytest.raises(BadResultCodeError):
                self.client.arm_away_instant(self.location_id)

            # should still be disarmed
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_away() is False
            assert self.client.locations[self.location_id].is_disarmed() is True

    def tests_arm_stay(self):
        """Test arm stay."""
        # first test with no issues
        self.client = create_client()
        responses = [RESPONSE_ARM_SUCCESS, RESPONSE_ARMED_STAY]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            self.client.arm_stay(self.location_id)

            # confirm armed_away
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_home() is True

        # second test with a zone faulted
        self.client = create_client()
        responses = [RESPONSE_ARM_FAILED, RESPONSE_DISARMED]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            with pytest.raises(BadResultCodeError):
                self.client.arm_stay(self.location_id)

            # should still be disarmed
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_home() is False
            assert self.client.locations[self.location_id].is_disarmed() is True

        # third test with bad usercode
        self.client = create_client()
        responses = [RESPONSE_USER_CODE_INVALID, RESPONSE_DISARMED]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            with pytest.raises(BadResultCodeError):
                self.client.arm_stay(self.location_id)

            # should still be disarmed
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_home() is False
            assert self.client.locations[self.location_id].is_disarmed() is True

    def tests_arm_stay_instant(self):
        """Test arm stay instant."""
        # first test with no issues
        self.client = create_client()
        responses = [RESPONSE_ARM_SUCCESS, RESPONSE_ARMED_STAY]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            self.client.arm_stay_instant(self.location_id)

            # confirm armed_away
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_home() is True

        # second test with a zone faulted
        self.client = create_client()
        responses = [RESPONSE_ARM_FAILED, RESPONSE_DISARMED]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            with pytest.raises(BadResultCodeError):
                self.client.arm_stay_instant(self.location_id)

            # should still be disarmed
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_home() is False
            assert self.client.locations[self.location_id].is_disarmed() is True

        # third test with bad usercode
        self.client = create_client()
        responses = [RESPONSE_USER_CODE_INVALID, RESPONSE_DISARMED]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            with pytest.raises(BadResultCodeError):
                self.client.arm_stay_instant(self.location_id)

            # should still be disarmed
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_home() is False
            assert self.client.locations[self.location_id].is_disarmed() is True

    def tests_arm_stay_night(self):
        """Test arm stay night."""
        # first test with no issues
        self.client = create_client()
        responses = [RESPONSE_ARM_SUCCESS, RESPONSE_ARMED_STAY_NIGHT]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            self.client.arm_stay_night(self.location_id)

            # confirm armed_away
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_night() is True

        # second test with a zone faulted
        self.client = create_client()
        responses = [RESPONSE_ARM_FAILED, RESPONSE_DISARMED]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            with pytest.raises(BadResultCodeError):
                self.client.arm_stay_night(self.location_id)

            # should still be disarmed
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_night() is False
            assert self.client.locations[self.location_id].is_disarmed() is True

        # third test with bad usercode
        self.client = create_client()
        responses = [RESPONSE_USER_CODE_INVALID, RESPONSE_DISARMED]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            with pytest.raises(BadResultCodeError):
                self.client.arm_stay_night(self.location_id)

            # should still be disarmed
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_night() is False
            assert self.client.locations[self.location_id].is_disarmed() is True

    def tests_disarm(self):
        """Test disarm."""
        # first test with no issues
        self.client = create_client()
        responses = [
            RESPONSE_ARM_SUCCESS,
            RESPONSE_ARMED_AWAY,
            RESPONSE_DISARM_SUCCESS,
            RESPONSE_DISARMED,
        ]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            # arm the system and confirm armed_away
            self.client.arm_away(self.location_id)
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_away() is True

            # now disarm
            self.client.disarm(self.location_id)
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_disarmed() is True

    def tests_disarm_command_failed(self):
        """Test disarm with command failed."""
        # first test with no issues
        self.client = create_client()
        responses = [
            RESPONSE_ARM_SUCCESS,
            RESPONSE_ARMED_AWAY,
            RESPONSE_DISARM_FAILED,
            RESPONSE_ARMED_AWAY,
        ]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            # arm the system and confirm armed_away
            self.client.arm_away(self.location_id)
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_away() is True

            # now disarm, should fail
            with pytest.raises(BadResultCodeError):
                self.client.disarm(self.location_id)

            # should still be armed_away
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_away() is True

    def tests_disarm_user_code_invalid(self):
        """Test disarm with invalid user code."""
        # first test with no issues
        self.client = create_client()
        responses = [
            RESPONSE_ARM_SUCCESS,
            RESPONSE_ARMED_AWAY,
            RESPONSE_USER_CODE_INVALID,
            RESPONSE_ARMED_AWAY,
        ]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            # arm the system and confirm armed_away
            self.client.arm_away(self.location_id)
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_away() is True

            with pytest.raises(BadResultCodeError):
                self.client.disarm(self.location_id)

            # should still be armed_away when disarming fails
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_away() is True

    def tests_disarm_disarmed(self):
        """Test attempt to disarm an already disarmed system."""
        # Did this once on my Lynx 7000 and it gave result code SUCCESS

        self.client = create_client()
        responses = [RESPONSE_DISARMED, RESPONSE_SUCCESS, RESPONSE_DISARMED]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_disarmed() is True

            # now disarm
            self.client.disarm(self.location_id)
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_disarmed() is True
