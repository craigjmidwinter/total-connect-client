"""Test client.validate_usercode()."""

import unittest
from unittest.mock import patch

import TotalConnectClient
from common import create_client
from const import LOCATION_INFO_BASIC_NORMAL

RESPONSE_VALID = {
    "ResultCode": TotalConnectClient.TotalConnectClient.SUCCESS,
    "ResultData": "None",
}

RESPONSE_INVALID = {
    "ResultCode": TotalConnectClient.TotalConnectClient.USER_CODE_INVALID,
    "ResultData": "None",
}

RESPONSE_UNAVAILABLE = {
    "ResultCode": TotalConnectClient.TotalConnectClient.USER_CODE_UNAVAILABLE,
    "ResultData": "None",
}

# random unknown response
RESPONSE_FAILED = {
    "ResultCode": TotalConnectClient.TotalConnectClient.COMMAND_FAILED,
    "ResultData": "None",
}


class TestTotalConnectClient(unittest.TestCase):
    """Test TotalConnectClient."""

    def setUp(self):
        """Test setup."""
        self.client = create_client()
        self.location_id = LOCATION_INFO_BASIC_NORMAL["LocationID"]

    def tearDown(self):
        """Test cleanup."""
        self.client = None

    def tests_validate_usercode(self):
        """Test validate_usercode() with a valid code."""
        RESPONSES = [
            RESPONSE_VALID,
            RESPONSE_INVALID,
            RESPONSE_UNAVAILABLE,
            RESPONSE_FAILED,
        ]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=RESPONSES
        ):
            # valid
            assert self.client.validate_usercode("1", "1234") is True
            # invalid
            assert self.client.validate_usercode("1", "1234") is False
            # unavailable
            assert self.client.validate_usercode("1", "1234") is False
            # other random failure
            assert self.client.validate_usercode("1", "1234") is False
