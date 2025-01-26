"""Test client authentication."""

import unittest
from unittest.mock import patch

import pytest
import requests_mock
from common import create_client
from const import LOCATION_INFO_BASIC_NORMAL

from total_connect_client.const import _ResultCode
from total_connect_client.client import TotalConnectClient
from total_connect_client.exceptions import AuthenticationError

RESPONSE_SUCCESS = {
    "ResultCode": _ResultCode.SUCCESS.value,
    "ResultData": "None",
    "SessionID": "123456890",
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
        with patch(
            "total_connect_client.client.TotalConnectClient.request",
            side_effect=responses,
        ):
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
        ]
        with patch(
            "total_connect_client.client.TotalConnectClient.request",
            side_effect=responses,
        ), patch(
            "total_connect_client.client.TotalConnectClient._make_locations",
            return_value=["fakelocations"],
        ):
            # ensure we start logged out (first SUCCESS)
            self.client.log_out()
            assert self.client.is_logged_in() is False

            # success (second SUCCESS)
            self.client.authenticate()
            assert self.client.is_logged_in() is True

            # bad user or pass
            with requests_mock.Mocker(real_http=True) as rm, pytest.raises(AuthenticationError):
                rm.post(TotalConnectClient.TOKEN_ENDPOINT, status_code=403)
                self.client.authenticate()
            assert self.client.is_logged_in() is False

            # authentication failed
            with pytest.raises(AuthenticationError):
                self.client.authenticate()
            assert self.client.is_logged_in() is False
