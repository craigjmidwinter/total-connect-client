"""Test total_connect_client."""

import unittest
from unittest.mock import patch

import pytest
from common import create_client
from const import (
    LOCATION_INFO_BASIC_NORMAL,
    RESPONSE_ARMED_AWAY,
    RESPONSE_DISARMED,
    RESPONSE_FEATURE_NOT_SUPPORTED,
)

from total_connect_client.exceptions import (
    FeatureNotSupportedError,
    PartialResponseError,
)

RESPONSE_DISARMED_NONE = {"ResultCode": 0}


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

    def tests_get_panel_meta_data_normal(self):
        """Test get_panel_meta_data() with a normal response."""
        responses = [RESPONSE_ARMED_AWAY, RESPONSE_DISARMED]
        with patch(
            "total_connect_client.client.TotalConnectClient.request",
            side_effect=responses,
        ):
            # should start disarmed
            assert self.location.arming_state.is_disarmed()

            # first response shows armed_away
            self.location.get_panel_meta_data()
            assert self.location.arming_state.is_armed_away()

            # second response shows disarmed
            self.location.get_panel_meta_data()
            assert self.location.arming_state.is_disarmed()

    def tests_get_panel_meta_data_none(self):
        """Test get_panel_meta_data() with an empty PanelMetadataAndStatus response."""
        responses = [RESPONSE_DISARMED_NONE]
        with patch(
            "total_connect_client.client.TotalConnectClient.request",
            side_effect=responses,
        ):
            # should start disarmed
            assert self.location.arming_state.is_disarmed()

            # first response gives empty status...should remain the same
            with pytest.raises(PartialResponseError):
                self.location.get_panel_meta_data()

            assert self.location.arming_state.is_disarmed()

    def tests_get_panel_meta_data_failed(self):
        """Test get_panel_meta_data() with an empty PanelMetadataAndStatus response."""
        responses = [RESPONSE_FEATURE_NOT_SUPPORTED]
        with patch(
            "total_connect_client.client.TotalConnectClient.request",
            side_effect=responses,
        ):
            # should start disarmed
            assert self.location.arming_state.is_disarmed()

            with pytest.raises(FeatureNotSupportedError):
                self.location.get_panel_meta_data()
