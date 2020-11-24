"""Test total_connect_client."""

import unittest
from unittest.mock import patch

from common import create_client
from const import (
    LOCATION_INFO_BASIC_NORMAL,
    RESPONSE_ARMED_AWAY,
    RESPONSE_ARMED_STAY,
    RESPONSE_ARMED_STAY_NIGHT,
    RESPONSE_DISARMED,
)
from TotalConnectClient import ZONE_STATUS_NORMAL


class TestTotalConnectClient(unittest.TestCase):
    """Test TotalConnectClient."""

    def setUp(self):
        """Test setup."""
        self.client = create_client()
        self.location_id = LOCATION_INFO_BASIC_NORMAL["LocationID"]

    def tearDown(self):
        """Test cleanup."""
        self.client = None

    def tests_zone_status(self):
        """Test zone_status."""
        responses = [RESPONSE_DISARMED]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            # should start disarmed
            assert self.client.locations[self.location_id].is_disarmed() is True

            # first ask for status of zone 1, which exists
            assert self.client.zone_status(self.location_id, "1") is ZONE_STATUS_NORMAL

            # first ask for status of zone 99, which does not exist
            assert self.client.zone_status(self.location_id, "99") is None

    def tests_get_armed_status(self):
        """Test get_armed_status."""
        responses = [
            RESPONSE_ARMED_STAY,
            RESPONSE_ARMED_STAY_NIGHT,
            RESPONSE_ARMED_AWAY,
            RESPONSE_DISARMED,
        ]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=responses
        ):
            # should start disarmed
            assert self.client.locations[self.location_id].is_disarmed() is True

            # armed_stay
            assert self.client.get_armed_status(self.location_id)
            assert self.client.locations[self.location_id].is_armed_home() is True

            # armed_stay_night
            assert self.client.get_armed_status(self.location_id)
            assert self.client.locations[self.location_id].is_armed_home() is True
            assert self.client.locations[self.location_id].is_armed_night() is True

            # armed_away
            assert self.client.get_armed_status(self.location_id)
            assert self.client.locations[self.location_id].is_armed_away() is True

            # TODO: test alarming states

            # disarmed
            assert self.client.get_armed_status(self.location_id)
            assert self.client.locations[self.location_id].is_disarmed() is True
