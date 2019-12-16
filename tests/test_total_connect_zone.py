"""Test total_connect_client."""

import unittest

import TotalConnectClient

ZONE_NORMAL = {
    "ZoneDescription": "Normal",
    "PartitionID": "1",
    "ZoneStatus": TotalConnectClient.ZONE_STATUS_NORMAL,
}

ZONE_BYPASSED = {
    "ZoneDescription": "Bypassed",
    "PartitionID": "1",
    "ZoneStatus": TotalConnectClient.ZONE_STATUS_BYPASSED,
}

ZONE_FAULTED = {
    "ZoneDescription": "Faulted",
    "PartitionID": "1",
    "ZoneStatus": TotalConnectClient.ZONE_STATUS_FAULT,
}

ZONE_TAMPERED = {
    "ZoneDescription": "Tampered",
    "PartitionID": "1",
    "ZoneStatus": TotalConnectClient.ZONE_STATUS_TAMPER,
}

ZONE_LOW_BATTERY = {
    "ZoneDescription": "Low Battery",
    "PartitionID": "1",
    "ZoneStatus": TotalConnectClient.ZONE_STATUS_LOW_BATTERY,
}

ZONE_TROUBLE_LOW_BATTERY = {
    "ZoneDescription": "Trouble Low Battery",
    "PartitionID": "1",
    "ZoneStatus": TotalConnectClient.ZONE_STATUS_TROUBLE_LOW_BATTERY,
}

ZONE_TRIGGERED = {
    "ZoneDescription": "Triggered",
    "PartitionID": "1",
    "ZoneStatus": TotalConnectClient.ZONE_STATUS_TRIGGERED,
}


class TestTotalConnectZone(unittest.TestCase):
    """Test TotalConnectZone."""

    def setUp(self):
        """Setup."""
        self.zone_normal = TotalConnectClient.TotalConnectZone(ZONE_NORMAL)
        self.zone_bypassed = TotalConnectClient.TotalConnectZone(ZONE_BYPASSED)
        self.zone_faulted = TotalConnectClient.TotalConnectZone(ZONE_FAULTED)
        self.zone_tampered = TotalConnectClient.TotalConnectZone(ZONE_TAMPERED)
        self.zone_low_battery = TotalConnectClient.TotalConnectZone(ZONE_LOW_BATTERY)
        self.zone_trouble_low_battery = TotalConnectClient.TotalConnectZone(
            ZONE_TROUBLE_LOW_BATTERY
        )
        self.zone_triggered = TotalConnectClient.TotalConnectZone(ZONE_TRIGGERED)

    def tearDown(self):
        """Tear down."""
        self.zone_normal = None
        self.zone_bypassed = None
        self.zone_faulted = None
        self.zone_tampered = None
        self.zone_low_battery = None
        self.zone_trouble_low_battery = None
        self.zone_triggered = None

    def tests_normal(self):
        """Normal zone."""
        self.assertFalse(self.zone_normal.is_bypassed())
        self.assertFalse(self.zone_normal.is_faulted())
        self.assertFalse(self.zone_normal.is_tampered())
        self.assertFalse(self.zone_normal.is_low_battery())
        self.assertFalse(self.zone_normal.is_troubled())
        self.assertFalse(self.zone_normal.is_triggered())

    def tests_bypassed(self):
        """Bypassed zone."""
        self.assertTrue(self.zone_bypassed.is_bypassed())
        self.assertFalse(self.zone_bypassed.is_faulted())
        self.assertFalse(self.zone_bypassed.is_tampered())
        self.assertFalse(self.zone_bypassed.is_low_battery())
        self.assertFalse(self.zone_bypassed.is_troubled())
        self.assertFalse(self.zone_bypassed.is_triggered())

    def tests_faulted(self):
        """Faulted zone."""
        self.assertFalse(self.zone_faulted.is_bypassed())
        self.assertTrue(self.zone_faulted.is_faulted())
        self.assertFalse(self.zone_faulted.is_tampered())
        self.assertFalse(self.zone_faulted.is_low_battery())
        self.assertFalse(self.zone_faulted.is_troubled())
        self.assertFalse(self.zone_faulted.is_triggered())

    def tests_tampered(self):
        """Faulted zone."""
        self.assertFalse(self.zone_tampered.is_bypassed())
        self.assertFalse(self.zone_tampered.is_faulted())
        self.assertTrue(self.zone_tampered.is_tampered())
        self.assertFalse(self.zone_tampered.is_low_battery())
        self.assertFalse(self.zone_tampered.is_troubled())
        self.assertFalse(self.zone_tampered.is_triggered())

    def tests_low_battery(self):
        """Zone with low battery."""
        self.assertFalse(self.zone_low_battery.is_bypassed())
        self.assertFalse(self.zone_low_battery.is_faulted())
        self.assertFalse(self.zone_low_battery.is_tampered())
        self.assertTrue(self.zone_low_battery.is_low_battery())
        self.assertFalse(self.zone_low_battery.is_troubled())
        self.assertFalse(self.zone_low_battery.is_triggered())

    def tests_trouble_low_battery(self):
        """Zone with low battery and trouble."""
        self.assertFalse(self.zone_trouble_low_battery.is_bypassed())
        self.assertFalse(self.zone_trouble_low_battery.is_faulted())
        self.assertFalse(self.zone_trouble_low_battery.is_tampered())
        self.assertTrue(self.zone_trouble_low_battery.is_low_battery())
        self.assertTrue(self.zone_trouble_low_battery.is_troubled())
        self.assertFalse(self.zone_trouble_low_battery.is_triggered())

    def tests_triggered(self):
        """Normal zone."""
        self.assertFalse(self.zone_triggered.is_bypassed())
        self.assertFalse(self.zone_triggered.is_faulted())
        self.assertFalse(self.zone_triggered.is_tampered())
        self.assertFalse(self.zone_triggered.is_low_battery())
        self.assertFalse(self.zone_triggered.is_troubled())
        self.assertTrue(self.zone_triggered.is_triggered())
