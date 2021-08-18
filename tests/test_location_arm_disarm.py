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
    RESPONSE_FEATURE_NOT_SUPPORTED,
)

from total_connect_client.client import ArmingHelper, TotalConnectClient
from total_connect_client.exceptions import AuthenticationError, BadResultCodeError

TCC_REQUEST_METHOD = "total_connect_client.client.TotalConnectClient.request"

RESPONSE_ARM_SUCCESS = {
    "ResultCode": TotalConnectClient.ARM_SUCCESS,
    "ResultData": "testing arm success",
}
RESPONSE_DISARM_SUCCESS = {
    "ResultCode": TotalConnectClient.DISARM_SUCCESS,
    "ResultData": "testing disarm success",
}

# returned when a zone is faulted
RESPONSE_ARM_FAILED = {
    "ResultCode": TotalConnectClient.COMMAND_FAILED,
    "ResultData": "testing arm failed",
}
RESPONSE_DISARM_FAILED = {
    "ResultCode": TotalConnectClient.COMMAND_FAILED,
    "ResultData": "testing disarm failed",
}

# appears to be for a bad/wrong code
RESPONSE_USER_CODE_INVALID = {
    "ResultCode": TotalConnectClient.USER_CODE_INVALID,
    "ResultData": "testing user code invalid",
}

# appears to be for a code entered for a wrong device/location
RESPONSE_USER_CODE_UNAVAILABLE = {
    "ResultCode": TotalConnectClient.USER_CODE_UNAVAILABLE,
    "ResultData": "testing user code unavailable",
}

RESPONSE_SUCCESS = {
    "ResultCode": TotalConnectClient.SUCCESS,
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
