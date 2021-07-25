"""Test total_connect_client location."""

import pytest
import unittest
from copy import deepcopy
from unittest.mock import Mock

from const import (
    LOCATION_INFO_BASIC_NORMAL,
    METADATA_DISARMED,
    METADATA_DISARMED_LOW_BATTERY,
    ZONE_DETAIL_STATUS,
)
from location import DEFAULT_USERCODE, TotalConnectLocation
from exceptions import PartialResponseError, TotalConnectError


class TestTotalConnectLocation(unittest.TestCase):
    """Test TotalConnectLocation."""

    def setUp(self):
        """Set up for location testing."""
        self.auto_bypass_low_battery = False
        self.location_normal = TotalConnectLocation(LOCATION_INFO_BASIC_NORMAL, self)
        self.location_normal.set_status(deepcopy(RESPONSE_DISARMED))
        self.location_normal.update_partitions(deepcopy(RESPONSE_DISARMED))
        self.location_normal.update_zones(deepcopy(RESPONSE_DISARMED))

    def tearDown(self):
        """Tear down."""
        self.location_normal = None

    def tests_basic(self):
        """Test basic attributes were set properly."""
        self.assertTrue(
            self.location_normal.location_id == LOCATION_INFO_BASIC_NORMAL["LocationID"]
        )
        self.assertTrue(
            self.location_normal.location_name
            == LOCATION_INFO_BASIC_NORMAL["LocationName"]
        )
        self.assertTrue(
            self.location_normal.security_device_id
            == LOCATION_INFO_BASIC_NORMAL["SecurityDeviceID"]
        )

    def tests_panel(self):
        """Test panel attributes."""
        self.assertFalse(self.location_normal.is_low_battery())
        self.assertFalse(self.location_normal.is_ac_loss())
        self.assertFalse(self.location_normal.is_cover_tampered())

    def tests_status(self):
        """Normal zone."""
        self.assertFalse(self.location_normal.is_arming())
        self.assertFalse(self.location_normal.is_disarming())
        self.assertTrue(self.location_normal.is_disarmed())
        self.assertFalse(self.location_normal.is_armed_away())
        self.assertFalse(self.location_normal.is_armed_custom_bypass())
        self.assertFalse(self.location_normal.is_armed_home())
        self.assertFalse(self.location_normal.is_armed_night())
        self.assertFalse(self.location_normal.is_armed())
        self.assertFalse(self.location_normal.is_pending())
        self.assertFalse(self.location_normal.is_triggered_police())
        self.assertFalse(self.location_normal.is_triggered_fire())
        self.assertFalse(self.location_normal.is_triggered_gas())
        self.assertFalse(self.location_normal.is_triggered())

        loc = TotalConnectLocation(LOCATION_INFO_BASIC_NORMAL, self)
        r = deepcopy(RESPONSE_DISARMED)
        r["PanelMetadataAndStatus"] = METADATA_DISARMED_LOW_BATTERY
        loc.update_zones(r)
        assert loc.zones["1"].is_low_battery() is True

    def tests_set_status_none(self):
        """Test set_status with None passed in."""
        loc = TotalConnectLocation(LOCATION_INFO_BASIC_NORMAL, self)
        loc.set_status(deepcopy(RESPONSE_DISARMED))
        loc.update_partitions(deepcopy(RESPONSE_DISARMED))
        loc.update_zones(deepcopy(RESPONSE_DISARMED))

        self.assertTrue(loc.is_disarmed())
        with pytest.raises(PartialResponseError):
            loc.set_status(None)

        data = deepcopy(RESPONSE_DISARMED)
        del data["PanelMetadataAndStatus"]["Partitions"]["PartitionInfo"]
        with pytest.raises(PartialResponseError):
            loc.update_partitions(data)
        del data["PanelMetadataAndStatus"]["Partitions"]
        with pytest.raises(PartialResponseError):
            loc.update_partitions(data)

        data = deepcopy(RESPONSE_DISARMED)
        del data["PanelMetadataAndStatus"]["Zones"]["ZoneInfo"]
        with pytest.raises(TotalConnectError):
            loc.update_zones(data)

        # See issue #112 when user's system returned zero zones,
        # and zeep set "Zones" to None
        data["PanelMetadataAndStatus"]["Zones"] = None
        with pytest.raises(TotalConnectError):
            loc.update_zones(data)

        del data["PanelMetadataAndStatus"]["Zones"]
        with pytest.raises(TotalConnectError):
            loc.update_zones(data)
        self.assertTrue(loc.is_disarmed())

    def tests_set_zone_details(self):
        """Test set_zone_details with normal data passed in."""
        self.location_normal.set_zone_details(RESPONSE_GET_ZONE_DETAILS_SUCCESS)

        # "Zones" is None
        r = deepcopy(RESPONSE_GET_ZONE_DETAILS_SUCCESS)
        r["ZoneStatus"]["Zones"] = None
        with pytest.raises(PartialResponseError):
            self.location_normal.set_zone_details(r)

        # "ZoneStatusInfoWithPartitionId" is None
        r = deepcopy(RESPONSE_GET_ZONE_DETAILS_SUCCESS)
        r["ZoneStatus"]["Zones"] = {"ZoneStatusInfoWithPartitionId": None}
        # now test with "ZoneInfo" is none
        with pytest.raises(PartialResponseError):
            self.location_normal.set_zone_details(r)

    def tests_auto_bypass_low_battery(self):
        """Test auto bypass of low battery zones."""

        mock_client = Mock()

        loc = TotalConnectLocation(LOCATION_INFO_BASIC_NORMAL, mock_client)

        # should not try to bypass by default
        assert loc.auto_bypass_low_battery is False
        r = deepcopy(RESPONSE_DISARMED)
        r["PanelMetadataAndStatus"] = METADATA_DISARMED_LOW_BATTERY
        loc.set_status(r)
        loc.update_partitions(r)
        loc.update_zones(r)
        assert mock_client.zone_bypass.call_count == 0

        # now set to auto bypass
        loc.auto_bypass_low_battery = True
        assert loc.auto_bypass_low_battery is True

        # now update status with a low battery and ensure it is bypassed
        loc.set_status(r)
        loc.update_partitions(r)
        loc.update_zones(r)
        assert mock_client.zone_bypass.call_count == 1

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
