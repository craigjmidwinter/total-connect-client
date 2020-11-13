"""Test total_connect_client."""

import unittest
from unittest.mock import patch

from common import create_client
from const import LOCATION_INFO_BASIC_NORMAL, RESPONSE_DISARMED
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
