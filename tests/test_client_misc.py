"""Test total_connect_client."""

import unittest
from unittest.mock import patch

import pytest
from common import create_client
from const import (
    LOCATION_INFO_BASIC_NORMAL,
    # RESPONSE_ARMED_AWAY,
    # RESPONSE_ARMED_STAY,
    # RESPONSE_ARMED_STAY_NIGHT,
    RESPONSE_DISARMED,
    RESPONSE_FEATURE_NOT_SUPPORTED,
    RESPONSE_GET_ZONE_DETAILS_NONE,
    RESPONSE_GET_ZONE_DETAILS_SUCCESS,
    RESPONSE_UNKNOWN,
)

from total_connect_client.zone import ZoneStatus

from total_connect_client.exceptions import (
    BadResultCodeError,
    TotalConnectError,
)


class TestTotalConnectClient(unittest.TestCase):
    """Test TotalConnectClient."""

    def setUp(self):
        """Test setup."""
        self.client = create_client()
        self.location_id = LOCATION_INFO_BASIC_NORMAL["LocationID"]
        self.location = self.client.locations[self.location_id]

    def tearDown(self):
        """Test cleanup."""
        self.client = None

    def tests_zone_status(self):
        """Test zone_status."""
        responses = [RESPONSE_DISARMED]
        with patch(
            "total_connect_client.client.TotalConnectClient.request",
            side_effect=responses,
        ):
            # should start disarmed
            assert self.location.arming_state.is_disarmed()

            # ask for status of zone 1, which exists
            assert self.location.zone_status("1") == ZoneStatus.NORMAL

            # ask for status of zone 99, which does not exist
            with pytest.raises(TotalConnectError):
                self.location.zone_status("99")

    def tests_get_zone_details(self):
        """Test get_zone_details."""
        responses = [
            RESPONSE_GET_ZONE_DETAILS_SUCCESS,
            RESPONSE_FEATURE_NOT_SUPPORTED,
            RESPONSE_UNKNOWN,
            RESPONSE_GET_ZONE_DETAILS_NONE,
        ]
        with patch(
            "total_connect_client.client.TotalConnectClient.request",
            side_effect=responses,
        ):
            # first response is SUCCESS
            self.location.get_zone_details()
            # second response is FEATURE_NOT_SUPPORTED
            self.location.get_zone_details()
            # third response is UNKNOWN
            with pytest.raises(BadResultCodeError):
                self.location.get_zone_details()
            # third response is SUCCESS but with empty ZoneStatus
            # ...which we've seen before in the wild
            self.location.get_zone_details()
