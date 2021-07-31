"""Test client authentication."""

from unittest.mock import patch
import unittest
import pytest

from total_connect_client.client import TotalConnectClient
from total_connect_client.exceptions import AuthenticationError
from common import create_client
from const import LOCATION_INFO_BASIC_NORMAL

RESPONSE_SUCCESS = {
    "ResultCode": TotalConnectClient.SUCCESS,
    "ResultData": "None",
    "SessionID": "123456890",
}

RESPONSE_BAD_USER_OR_PASSWORD = {
    "ResultCode": TotalConnectClient.BAD_USER_OR_PASSWORD,
    "ResultData": "None",
}

RESPONSE_AUTHENTICATION_FAILED = {
    "ResultCode": TotalConnectClient.AUTHENTICATION_FAILED,
    "ResultData": "None",
}

# random unknown response
RESPONSE_INVALID_SESSION = {
    "ResultCode": TotalConnectClient.INVALID_SESSION,
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

    def tests_logout(self):
        """Test logout."""
        responses = [
            RESPONSE_SUCCESS,
        ]
        with patch("total_connect_client.client.TotalConnectClient.request", side_effect=responses):
            assert self.client.is_logged_in() is True
            self.client.log_out()
            assert self.client.is_logged_in() is False

            # succeeds because we are logged out
            self.client.log_out()

    def tests_authenticate(self):
        """Test authenticate()."""
        responses = [
            RESPONSE_SUCCESS,
            RESPONSE_SUCCESS,
            RESPONSE_BAD_USER_OR_PASSWORD,
            RESPONSE_AUTHENTICATION_FAILED,
        ]
        with patch("total_connect_client.client.TotalConnectClient.request", side_effect=responses), patch(
            "total_connect_client.client.TotalConnectClient._make_locations", return_value=["fakelocations"]
        ):
            # ensure we start logged out (first SUCCESS)
            self.client.log_out()
            assert self.client.is_logged_in() is False

            # success (second SUCCESS)
            self.client.authenticate()
            assert self.client.is_logged_in() is True
            assert self.client.is_valid_credentials() is True

            # bad user or pass
            with pytest.raises(AuthenticationError):
                self.client.authenticate()
            assert self.client.is_logged_in() is False
            assert self.client.is_valid_credentials() is False

            # authentication failed
            with pytest.raises(AuthenticationError):
                self.client.authenticate()
            assert self.client.is_logged_in() is False
            assert self.client.is_valid_credentials() is False
