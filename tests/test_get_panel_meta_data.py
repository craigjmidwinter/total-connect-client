"""Test total_connect_client."""

import unittest
from unittest.mock import patch

from common import create_client
from const import LOCATION_INFO_BASIC_NORMAL, RESPONSE_ARMED_AWAY, RESPONSE_DISARMED

RESPONSE_DISARMED_NONE = {"ResultCode": 0}


class TestTotalConnectClient(unittest.TestCase):
    """Test TotalConnectClient."""

    def setUp(self):
        """Test setup."""
        self.client = create_client()
        self.location_id = LOCATION_INFO_BASIC_NORMAL["LocationID"]

    def tearDown(self):
        """Test cleanup."""
        self.client = None

    def tests_get_panel_meta_data_normal(self):
        """Test get_panel_meta_data() with a normal response."""

        RESPONSES = [RESPONSE_ARMED_AWAY, RESPONSE_DISARMED]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=RESPONSES,
        ):
            # should start disarmed
            assert self.client.locations[self.location_id].is_disarmed() is True

            # first response shows armed_away
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_armed_away() is True

            # second response shows disarmed
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_disarmed() is True

    def tests_get_panel_meta_data_none(self):
        """Test get_panel_meta_data() with an empty PanelMetadataAndStatus response."""

        RESPONSES = [RESPONSE_DISARMED_NONE]
        with patch(
            "TotalConnectClient.TotalConnectClient.request", side_effect=RESPONSES,
        ):
            # should start disarmed
            assert self.client.locations[self.location_id].is_disarmed() is True

            # first response gives empty status...should remain the same
            self.client.get_panel_meta_data(self.location_id)
            assert self.client.locations[self.location_id].is_disarmed() is True
