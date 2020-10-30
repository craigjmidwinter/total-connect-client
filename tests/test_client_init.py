"""Test total_connect_client."""

import unittest
from unittest.mock import patch

import TotalConnectClient
from const import (
    RESPONSE_AUTHENTICATE,
    RESPONSE_DISARMED,
    RESPONSE_GET_ZONE_DETAILS_SUCCESS,
)


class TestTotalConnectClient(unittest.TestCase):
    """Test TotalConnectClient."""

    def setUp(self):
        """Test setup."""
        self.client = None
        # self.location_id = LOCATION_INFO_BASIC_NORMAL["LocationID"]

    def tearDown(self):
        """Test cleanup."""
        self.client = None

    def tests_init_usercodes_none(self):
        """Test init with usercodes == None."""
        RESPONSES = [
            RESPONSE_AUTHENTICATE,
            RESPONSE_GET_ZONE_DETAILS_SUCCESS,
            RESPONSE_DISARMED,
        ]

        with patch("zeep.Client", autospec=True), patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=RESPONSES
        ) as mock_request:
            client = TotalConnectClient.TotalConnectClient(
                "username", "password", usercodes=None
            )
            assert mock_request.call_count == 3

        assert client.usercodes == {"default": TotalConnectClient.DEFAULT_USERCODE}

    def tests_init_usercodes_string(self):
        """Test init with usercodes == a string."""
        RESPONSES = [
            RESPONSE_AUTHENTICATE,
            RESPONSE_GET_ZONE_DETAILS_SUCCESS,
            RESPONSE_DISARMED,
        ]

        with patch("zeep.Client", autospec=True), patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=RESPONSES
        ) as mock_request:
            client = TotalConnectClient.TotalConnectClient(
                "username", "password", usercodes="123456"
            )
            assert mock_request.call_count == 3

        assert client.usercodes == {"default": TotalConnectClient.DEFAULT_USERCODE}
