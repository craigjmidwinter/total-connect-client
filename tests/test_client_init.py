"""Test total_connect_client."""

import unittest
from unittest.mock import patch

import pytest
import TotalConnectClient
from const import (
    LOCATION_INFO_BASIC_NORMAL,
    RESPONSE_AUTHENTICATE,
    RESPONSE_AUTHENTICATE_EMPTY,
    RESPONSE_DISARMED,
    RESPONSE_GET_ZONE_DETAILS_SUCCESS,
    RESPONSE_PARTITION_DETAILS,
)
from exceptions import TotalConnectError


class TestTotalConnectClient(unittest.TestCase):
    """Test TotalConnectClient."""

    def setUp(self):
        """Test setup."""
        self.client = None
        self.location_id = LOCATION_INFO_BASIC_NORMAL["LocationID"]

    def tearDown(self):
        """Test cleanup."""
        self.client = None

    def tests_init_usercodes_none(self):
        """Test init with usercodes == None."""
        responses = [
            RESPONSE_AUTHENTICATE,
            RESPONSE_PARTITION_DETAILS,
            RESPONSE_GET_ZONE_DETAILS_SUCCESS,
            RESPONSE_DISARMED,
        ]

        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ) as mock_request:
            client = TotalConnectClient.TotalConnectClient(
                "username", "password", usercodes=None
            )
            assert mock_request.call_count == 1
            if client.locations:  # force client to fetch them
                pass
            assert mock_request.call_count == 4


    def tests_init_locations_empty(self):
        """Test init with no locations."""
        responses = [
            RESPONSE_AUTHENTICATE_EMPTY,
        ]

        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ) as mock_request, pytest.raises(TotalConnectError):

            TotalConnectClient.TotalConnectClient("username", "password", usercodes=None)

    def tests_init_usercodes_string(self):
        """Test init with usercodes == a string."""
        responses = [
            RESPONSE_AUTHENTICATE,
            RESPONSE_PARTITION_DETAILS,
            RESPONSE_GET_ZONE_DETAILS_SUCCESS,
            RESPONSE_DISARMED,
        ]

        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ) as mock_request:
            with pytest.raises(AttributeError):
                # string is not a valid type for usercodes (only dict)
                TotalConnectClient.TotalConnectClient(
                    "username", "password", usercodes="123456"
                )
