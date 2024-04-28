"""Test total_connect_client location."""

import unittest
from copy import deepcopy
from unittest.mock import Mock, patch

import pytest
from const import (
    LOCATION_INFO_BASIC_NORMAL,
    METADATA_DISARMED,
    METADATA_DISARMED_LOW_BATTERY,
    RESPONSE_DISARMED,
    RESPONSE_GET_ZONE_DETAILS_SUCCESS,
)

from total_connect_client.const import ArmingState
from total_connect_client.exceptions import PartialResponseError, TotalConnectError
from total_connect_client.location import DEFAULT_USERCODE, TotalConnectLocation


class TestTotalConnectLocation(unittest.TestCase):
    """Test TotalConnectLocation."""

    def setUp(self):
        """Set up for location testing."""
        self.auto_bypass_low_battery = False
        self.location_normal = TotalConnectLocation(LOCATION_INFO_BASIC_NORMAL, self)
        self.location_normal._update_status(deepcopy(RESPONSE_DISARMED))
        self.location_normal._update_partitions(deepcopy(RESPONSE_DISARMED))
        self.location_normal._update_zones(deepcopy(RESPONSE_DISARMED))

    def tearDown(self):
        """Tear down."""
        self.location_normal = None

    def tests_basic(self):
        """Test basic attributes were set properly."""
        self.assertTrue(
            self.location_normal.location_id == LOCATION_INFO_BASIC_NORMAL["LocationID"]
        )
        lname = LOCATION_INFO_BASIC_NORMAL["LocationName"]
        self.assertTrue(self.location_normal.location_name == lname)
        lsdid = LOCATION_INFO_BASIC_NORMAL["SecurityDeviceID"]
        self.assertTrue(self.location_normal.security_device_id == lsdid)

    def tests_panel(self):
        """Test panel attributes."""
        self.assertFalse(self.location_normal.is_low_battery())
        self.assertFalse(self.location_normal.is_ac_loss())
        self.assertFalse(self.location_normal.is_cover_tampered())

    def tests_status(self):
        """Normal zone."""
        self.assertFalse(self.location_normal.arming_state.is_arming())
        self.assertFalse(self.location_normal.arming_state.is_disarming())
        self.assertTrue(self.location_normal.arming_state.is_disarmed())
        self.assertFalse(self.location_normal.arming_state.is_armed_away())
        self.assertFalse(self.location_normal.arming_state.is_armed_custom_bypass())
        self.assertFalse(self.location_normal.arming_state.is_armed_home())
        self.assertFalse(self.location_normal.arming_state.is_armed_night())
        self.assertFalse(self.location_normal.arming_state.is_armed())
        self.assertFalse(self.location_normal.arming_state.is_pending())
        self.assertFalse(self.location_normal.arming_state.is_triggered_police())
        self.assertFalse(self.location_normal.arming_state.is_triggered_fire())
        self.assertFalse(self.location_normal.arming_state.is_triggered_gas())
        self.assertFalse(self.location_normal.arming_state.is_triggered())

        loc = TotalConnectLocation(LOCATION_INFO_BASIC_NORMAL, self)
        response = deepcopy(RESPONSE_DISARMED)
        response["PanelMetadataAndStatus"] = METADATA_DISARMED_LOW_BATTERY
        loc._update_zones(response)
        assert loc.zones["1"].is_low_battery() is True

    def tests_update_status_none(self):
        """Test _update_status with None passed in."""
        loc = TotalConnectLocation(LOCATION_INFO_BASIC_NORMAL, self)
        loc._update_status(deepcopy(RESPONSE_DISARMED))
        loc._update_partitions(deepcopy(RESPONSE_DISARMED))
        loc._update_zones(deepcopy(RESPONSE_DISARMED))

        self.assertTrue(loc.arming_state.is_disarmed())
        with pytest.raises(PartialResponseError):
            loc._update_status(None)

        data = deepcopy(RESPONSE_DISARMED)
        del data["PanelMetadataAndStatus"]["Partitions"]["PartitionInfo"]
        with pytest.raises(PartialResponseError):
            loc._update_partitions(data)
        del data["PanelMetadataAndStatus"]["Partitions"]
        with pytest.raises(PartialResponseError):
            loc._update_partitions(data)

        data = deepcopy(RESPONSE_DISARMED)
        del data["PanelMetadataAndStatus"]["Zones"]["ZoneInfo"]
        with pytest.raises(TotalConnectError):
            loc._update_zones(data)

        # See issue #112 when user's system returned zero zones,
        # and zeep set "Zones" to None
        data["PanelMetadataAndStatus"]["Zones"] = None
        with pytest.raises(TotalConnectError):
            loc._update_zones(data)

        del data["PanelMetadataAndStatus"]["Zones"]
        with pytest.raises(TotalConnectError):
            loc._update_zones(data)
        self.assertTrue(loc.arming_state.is_disarmed())

    def tests_set_zone_details(self):
        """Test set_zone_details with normal data passed in."""
        location = TotalConnectLocation(LOCATION_INFO_BASIC_NORMAL, None)
        location._update_zone_details(RESPONSE_GET_ZONE_DETAILS_SUCCESS)
        assert len(location.zones) == 1

        location = TotalConnectLocation(LOCATION_INFO_BASIC_NORMAL, None)
        # "Zones" is None, as seen in #112 and #205
        response = deepcopy(RESPONSE_GET_ZONE_DETAILS_SUCCESS)
        response["ZoneStatus"]["Zones"] = None
        location._update_zone_details(response)
        assert len(location.zones) == 0

        # "ZoneStatusInfoWithPartitionId" is None
        location = TotalConnectLocation(LOCATION_INFO_BASIC_NORMAL, None)
        response = deepcopy(RESPONSE_GET_ZONE_DETAILS_SUCCESS)
        response["ZoneStatus"]["Zones"] = {"ZoneStatusInfoWithPartitionId": None}
        location._update_zone_details(response)
        assert len(location.zones) == 0

    def tests_auto_bypass_low_battery(self):
        """Test auto bypass of low battery zones."""

        mock_client = Mock()
        loc = TotalConnectLocation(LOCATION_INFO_BASIC_NORMAL, mock_client)

        # should not try to bypass by default
        assert loc.auto_bypass_low_battery is False
        response = deepcopy(RESPONSE_DISARMED)
        response["PanelMetadataAndStatus"] = METADATA_DISARMED_LOW_BATTERY

        zbp = "total_connect_client.client.TotalConnectLocation.zone_bypass"
        with patch(zbp) as mock:
            loc._update_status(response)
            loc._update_partitions(response)
            loc._update_zones(response)
            assert mock.call_count == 0

        # now set to auto bypass
        loc.auto_bypass_low_battery = True

        # now update status with a low battery and ensure it is bypassed
        with patch(zbp) as mock:
            loc._update_status(response)
            loc._update_partitions(response)
            loc._update_zones(response)
            assert mock.call_count == 1

    def tests_set_usercode(self):
        """Test set_usercode."""

        mock_client = Mock()

        loc = TotalConnectLocation(LOCATION_INFO_BASIC_NORMAL, mock_client)

        # should start with default usercode
        assert loc.usercode == DEFAULT_USERCODE

        # now set it with an invalid code
        mock_client.validate_usercode.return_value = False
        assert loc.set_usercode("0000") is False
        assert loc.usercode == DEFAULT_USERCODE
        assert mock_client.validate_usercode.call_count == 1

        # now set it with a valid code
        mock_client.validate_usercode.return_value = True
        assert loc.set_usercode("1234") is True
        assert loc.usercode == "1234"
        assert mock_client.validate_usercode.call_count == 2


def tests_update_status():
    """Test location._update_status()."""
    location = TotalConnectLocation(LOCATION_INFO_BASIC_NORMAL, Mock())

    # known arming state should not produce an error
    response = {
        "PanelMetadataAndStatus": METADATA_DISARMED,
        "ArmingState": ArmingState.DISARMED,
    }
    location._update_status(response)
    assert location.arming_state == ArmingState.DISARMED

    # unknown arming state should produce an error
    with pytest.raises(TotalConnectError):
        response["ArmingState"] = 99999
        location._update_status(response)
