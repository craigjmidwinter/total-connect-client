"""Test total_connect_client."""

import unittest
from unittest.runner import TextTestRunner

import pytest
import TotalConnectClient
from const import (
    ZONE_STATUS_LYRIC_CONTACT,
    ZONE_STATUS_LYRIC_LOCAL_ALARM,
    ZONE_STATUS_LYRIC_MOTION,
    ZONE_STATUS_LYRIC_POLICE,
    ZONE_STATUS_LYRIC_TEMP,
    ZONE_STATUS_NORMAL,
    ZONE_LOW_BATTERY,
)
from zone import TotalConnectZone as tcz
from zone import (
    ZONE_TYPE_SECURITY, ZONE_STATUS_BYPASSED, ZONE_STATUS_FAULT,
    ZONE_STATUS_TROUBLE, ZONE_STATUS_TRIGGERED, ZONE_TYPE_FIRE_SMOKE,
    ZONE_TYPE_CARBON_MONOXIDE, ZONE_TYPE_PROA7_MEDICAL,
)


ZONE_BYPASSED = {
    "ZoneDescription": "Bypassed",
    "PartitionId": "1",
    "ZoneTypeId": ZONE_TYPE_SECURITY,
    "CanBeBypassed": 1,
    "ZoneStatus": ZONE_STATUS_BYPASSED,
}

ZONE_FAULTED = {
    "ZoneDescription": "Faulted",
    "ZoneID": "1",
    "PartitionId": "1",
    "ZoneTypeId": ZONE_TYPE_SECURITY,
    "CanBeBypassed": 1,
    "ZoneStatus": ZONE_STATUS_FAULT,
}

ZONE_TAMPERED = {
    "ZoneDescription": "Tampered",
    "PartitionId": "1",
    "ZoneTypeId": ZONE_TYPE_SECURITY,
    "CanBeBypassed": 1,
    "ZoneStatus": ZONE_STATUS_TROUBLE,
}

ZONE_BYPASSED_LOW_BATTERY = {
    "ZoneDescription": "Bypassed Low Battery",
    "PartitionId": "1",
    "ZoneTypeId": ZONE_TYPE_SECURITY,
    "CanBeBypassed": 1,
    "ZoneStatus": 65,
}

ZONE_TROUBLE_LOW_BATTERY = {
    "ZoneDescription": "Trouble Low Battery",
    "PartitionId": "1",
    "ZoneTypeId": ZONE_TYPE_SECURITY,
    "CanBeBypassed": 1,
    "ZoneStatus": 72,
}

ZONE_TRIGGERED = {
    "ZoneDescription": "Triggered",
    "PartitionId": "1",
    "ZoneTypeId": ZONE_TYPE_SECURITY,
    "CanBeBypassed": 1,
    "ZoneStatus": ZONE_STATUS_TRIGGERED,
}

ZONE_BUTTON = {
    "ZoneDescription": "Button",
    "PartitionId": "1",
    "ZoneTypeId": ZONE_TYPE_SECURITY,
    "CanBeBypassed": 0,
    "ZoneStatus": ZONE_STATUS_NORMAL,
}

ZONE_SMOKE = {
    "ZoneDescription": "Smoke",
    "PartitionId": "1",
    "ZoneTypeId": ZONE_TYPE_FIRE_SMOKE,
    "CanBeBypassed": 0,
    "ZoneStatus": ZONE_STATUS_NORMAL,
}

ZONE_GAS = {
    "ZoneDescription": "Gas",
    "PartitionId": "1",
    "ZoneTypeId": ZONE_TYPE_CARBON_MONOXIDE,
    "CanBeBypassed": 0,
    "ZoneStatus": ZONE_STATUS_NORMAL,
}


class TestTotalConnectZone(unittest.TestCase):
    """Test TotalConnectZone."""

    def setUp(self):
        """Test setup."""
        self.zone_normal = tcz(ZONE_STATUS_NORMAL)
        self.zone_bypassed = tcz(ZONE_BYPASSED)
        self.zone_faulted = tcz(ZONE_FAULTED)
        self.zone_tampered = tcz(ZONE_TAMPERED)
        self.zone_low_battery = tcz(ZONE_LOW_BATTERY)
        self.zone_bypassed_low_battery = tcz(ZONE_BYPASSED_LOW_BATTERY)
        self.zone_trouble_low_battery = tcz(ZONE_TROUBLE_LOW_BATTERY)
        self.zone_triggered = tcz(ZONE_TRIGGERED)
        self.zone_button = tcz(ZONE_BUTTON)
        self.zone_smoke = tcz(ZONE_SMOKE)
        self.zone_gas = tcz(ZONE_GAS)
        self.zone_lyric_contact = tcz(ZONE_STATUS_LYRIC_CONTACT)
        self.zone_lyric_motion = tcz(ZONE_STATUS_LYRIC_MOTION)
        self.zone_lyric_police = tcz(ZONE_STATUS_LYRIC_POLICE)
        self.zone_lyric_temp = tcz(ZONE_STATUS_LYRIC_TEMP)
        self.zone_lyric_local_alarm = tcz(ZONE_STATUS_LYRIC_LOCAL_ALARM)

    def tearDown(self):
        """Tear down."""
        self.zone_normal = None
        self.zone_bypassed = None
        self.zone_faulted = None
        self.zone_tampered = None
        self.zone_low_battery = None
        self.zone_trouble_low_battery = None
        self.zone_triggered = None
        self.zone_button = None
        self.zone_smoke = None
        self.zone_gas = None
        self.zone_lyric_contact = None
        self.zone_lyric_motion = None
        self.zone_lyric_police = None
        self.zone_lyric_temp = None
        self.zone_lyric_local_alarm = None

    def tests_normal(self):
        """Normal zone."""
        self.assertFalse(self.zone_normal.is_bypassed())
        self.assertFalse(self.zone_normal.is_faulted())
        self.assertFalse(self.zone_normal.is_tampered())
        self.assertFalse(self.zone_normal.is_low_battery())
        self.assertFalse(self.zone_normal.is_troubled())
        self.assertFalse(self.zone_normal.is_triggered())

    def tests_update(self):
        """Test updates to a zone."""
        self.assertFalse(self.zone_normal.is_faulted())
        self.zone_normal.update(ZONE_FAULTED)
        self.assertTrue(self.zone_normal.is_faulted())
        self.zone_normal.update(ZONE_STATUS_NORMAL)
        self.assertFalse(self.zone_normal.is_faulted())

        self.assertFalse(self.zone_normal.is_low_battery())
        self.zone_normal.update(ZONE_LOW_BATTERY)
        self.assertTrue(self.zone_normal.is_low_battery())
        self.zone_normal.update(ZONE_STATUS_NORMAL)
        self.assertFalse(self.zone_normal.is_low_battery())

    def tests_update_wrong_zone(self):
        """Test updates to the wrong zone."""
        zone_temp = ZONE_STATUS_NORMAL.copy()
        zone_temp["ZoneID"] = "99"
        with pytest.raises(Exception):
            assert self.zone_normal.update(zone_temp)

    def tests_bypassed(self):
        """Bypassed zone."""
        self.assertTrue(self.zone_bypassed.is_bypassed())
        self.assertFalse(self.zone_bypassed.is_faulted())
        self.assertFalse(self.zone_bypassed.is_tampered())
        self.assertFalse(self.zone_bypassed.is_low_battery())
        self.assertFalse(self.zone_bypassed.is_troubled())
        self.assertFalse(self.zone_bypassed.is_triggered())

    def tests_bypass(self):
        """Bypass a zone."""
        self.assertFalse(self.zone_normal.is_bypassed())
        self.zone_normal._mark_as_bypassed()
        self.assertTrue(self.zone_normal.is_bypassed())

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
        self.assertTrue(self.zone_tampered.is_troubled())
        self.assertFalse(self.zone_tampered.is_triggered())

    def tests_low_battery(self):
        """Zone with low battery."""
        self.assertFalse(self.zone_low_battery.is_bypassed())
        self.assertFalse(self.zone_low_battery.is_faulted())
        self.assertFalse(self.zone_low_battery.is_tampered())
        self.assertTrue(self.zone_low_battery.is_low_battery())
        self.assertFalse(self.zone_low_battery.is_troubled())
        self.assertFalse(self.zone_low_battery.is_triggered())

    def tests_bypassed_low_battery(self):
        """Zone bypassed with low battery."""
        self.assertTrue(self.zone_bypassed_low_battery.is_bypassed())
        self.assertFalse(self.zone_bypassed_low_battery.is_faulted())
        self.assertFalse(self.zone_bypassed_low_battery.is_tampered())
        self.assertTrue(self.zone_bypassed_low_battery.is_low_battery())
        self.assertFalse(self.zone_bypassed_low_battery.is_troubled())
        self.assertFalse(self.zone_bypassed_low_battery.is_triggered())

    def tests_trouble_low_battery(self):
        """Zone with low battery and trouble."""
        self.assertFalse(self.zone_trouble_low_battery.is_bypassed())
        self.assertFalse(self.zone_trouble_low_battery.is_faulted())
        self.assertTrue(self.zone_trouble_low_battery.is_tampered())
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

    def tests_type_button(self):
        """Button zone."""
        self.assertFalse(self.zone_normal.is_type_button())
        self.assertTrue(self.zone_button.is_type_button())
        self.assertFalse(self.zone_smoke.is_type_button())
        self.assertFalse(self.zone_gas.is_type_button())
        self.assertFalse(self.zone_lyric_contact.is_type_button())
        self.assertFalse(self.zone_lyric_local_alarm.is_type_button())
        self.assertFalse(self.zone_lyric_motion.is_type_button())
        self.assertFalse(self.zone_lyric_police.is_type_button())
        self.assertFalse(self.zone_lyric_temp.is_type_button())

    def tests_type_security(self):
        """Security zone."""
        self.assertTrue(self.zone_normal.is_type_security())
        self.assertTrue(self.zone_button.is_type_security())
        self.assertFalse(self.zone_smoke.is_type_security())
        self.assertFalse(self.zone_gas.is_type_security())
        self.assertTrue(self.zone_lyric_contact.is_type_security())
        self.assertTrue(self.zone_lyric_local_alarm.is_type_security())
        self.assertTrue(self.zone_lyric_motion.is_type_security())
        self.assertTrue(self.zone_lyric_police.is_type_security())
        self.assertFalse(self.zone_lyric_temp.is_type_security())

    def tests_type_fire(self):
        """Fire zone."""
        self.assertFalse(self.zone_normal.is_type_fire())
        self.assertFalse(self.zone_button.is_type_fire())
        self.assertTrue(self.zone_smoke.is_type_fire())
        self.assertFalse(self.zone_gas.is_type_fire())
        self.assertFalse(self.zone_lyric_contact.is_type_fire())
        self.assertFalse(self.zone_lyric_local_alarm.is_type_fire())
        self.assertFalse(self.zone_lyric_motion.is_type_fire())
        self.assertFalse(self.zone_lyric_police.is_type_fire())
        self.assertTrue(self.zone_lyric_temp.is_type_fire())

    def tests_type_carbon_monoxide(self):
        """Carbon monoxide zone."""
        self.assertFalse(self.zone_normal.is_type_carbon_monoxide())
        self.assertFalse(self.zone_button.is_type_carbon_monoxide())
        self.assertFalse(self.zone_smoke.is_type_carbon_monoxide())
        self.assertTrue(self.zone_gas.is_type_carbon_monoxide())
        self.assertFalse(self.zone_lyric_contact.is_type_carbon_monoxide())
        self.assertFalse(self.zone_lyric_local_alarm.is_type_carbon_monoxide())
        self.assertFalse(self.zone_lyric_motion.is_type_carbon_monoxide())
        self.assertFalse(self.zone_lyric_police.is_type_carbon_monoxide())
        self.assertFalse(self.zone_lyric_temp.is_type_carbon_monoxide())

    def tests_type_motion(self):
        """Motion zone."""
        self.assertFalse(self.zone_normal.is_type_motion())
        self.assertFalse(self.zone_button.is_type_motion())
        self.assertFalse(self.zone_smoke.is_type_motion())
        self.assertFalse(self.zone_gas.is_type_motion())
        self.assertFalse(self.zone_lyric_contact.is_type_motion())
        self.assertFalse(self.zone_lyric_local_alarm.is_type_motion())
        self.assertTrue(self.zone_lyric_motion.is_type_motion())
        self.assertFalse(self.zone_lyric_police.is_type_motion())
        self.assertFalse(self.zone_lyric_temp.is_type_motion())

def test_proa7_zones():
    """Test ProA7."""

    ZONE_MEDICAL = {
        "ZoneDescription": "Gas",
        "PartitionId": "1",
        "ZoneTypeId": ZONE_TYPE_PROA7_MEDICAL,
        "CanBeBypassed": 0,
        "ZoneStatus": ZONE_STATUS_NORMAL,
    }

    zone = tcz(ZONE_MEDICAL)
    assert zone.is_type_medical() is True
    assert zone.is_type_button() is True
