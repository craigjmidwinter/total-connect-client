"""Test total_connect_client location."""

import unittest
from unittest.mock import Mock

from copy import deepcopy

import TotalConnectClient
from const import LOCATION_INFO_BASIC_NORMAL, METADATA_DISARMED, METADATA_DISARMED_LOW_BATTERY, ZONE_DETAIL_STATUS


class TestTotalConnectLocation(unittest.TestCase):
    """Test TotalConnectLocation."""

    def setUp(self):
        """Set up for location testing."""
        self.auto_bypass_low_battery = False
        self.location_normal = TotalConnectClient.TotalConnectLocation(
            LOCATION_INFO_BASIC_NORMAL, self
        )
        self.location_normal.set_status(deepcopy(METADATA_DISARMED))

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

        loc = TotalConnectClient.TotalConnectLocation(LOCATION_INFO_BASIC_NORMAL, self)
        self.assertTrue(loc.set_status(deepcopy(METADATA_DISARMED_LOW_BATTERY)))
        print(loc)
        assert loc.zones["1"].is_low_battery() is True

    def tests_set_status_none(self):
        """Test set_status with None passed in."""
        loc = TotalConnectClient.TotalConnectLocation(LOCATION_INFO_BASIC_NORMAL, self)
        loc.set_status(deepcopy(METADATA_DISARMED))

        self.assertTrue(loc.is_disarmed())
        self.assertFalse(loc.set_status(None))

        data = deepcopy(METADATA_DISARMED)
        del data["Partitions"]["PartitionInfo"]
        self.assertFalse(loc.set_status(data))
        del data["Partitions"]
        self.assertFalse(loc.set_status(data))

        data = deepcopy(METADATA_DISARMED)
        del data["Zones"]["ZoneInfo"]
        self.assertFalse(loc.set_status(data))
        del data["Zones"]
        self.assertFalse(loc.set_status(data))
        self.assertTrue(loc.is_disarmed())

    def tests_set_zone_details(self):
        """Test set_zone_details with normal data passed in."""
        self.assertTrue(self.location_normal.set_zone_details(ZONE_DETAIL_STATUS))

        # "Zones" is None
        self.assertFalse(self.location_normal.set_zone_details({"Zones": None}))

        # "ZoneStatusInfoWithPartitionId" is None
        data = deepcopy(ZONE_DETAIL_STATUS)
        data["Zones"] = {"ZoneStatusInfoWithPartitionId": None}
        # now test with "ZoneInfo" is none
        self.assertFalse(self.location_normal.set_zone_details(data))

    def tests_auto_bypass_low_battery(self):
        """Test auto bypass of low battery zones."""

        mock_client = Mock()

        loc = TotalConnectClient.TotalConnectLocation(
            LOCATION_INFO_BASIC_NORMAL, mock_client
        )

        # should not try to bypass by default
        assert loc.auto_bypass_low_battery is False
        loc.set_status(METADATA_DISARMED_LOW_BATTERY)
        assert mock_client.zone_bypass.call_count == 0

        # now set to auto bypass
        loc.auto_bypass_low_battery = True
        assert loc.auto_bypass_low_battery is True

        # now update status with a low battery and ensure it is bypassed
        loc.set_status(METADATA_DISARMED_LOW_BATTERY)
        assert mock_client.zone_bypass.call_count == 1
        