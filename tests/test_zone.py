"""Test total_connect_client."""

import unittest
from unittest.mock import Mock

import pytest
from const import (
    ZONE_LOW_BATTERY,
    ZONE_STATUS_LYRIC_CONTACT,
    ZONE_STATUS_LYRIC_LOCAL_ALARM,
    ZONE_STATUS_LYRIC_KEYPAD,
    ZONE_STATUS_LYRIC_MOTION,
    ZONE_STATUS_LYRIC_POLICE,
    ZONE_STATUS_LYRIC_TEMP,
    ZS_NORMAL,
)

from total_connect_client.zone import ZoneStatus, ZoneType
from total_connect_client.zone import TotalConnectZone as tcz
from total_connect_client.exceptions import TotalConnectError

ZONE_BYPASSED = {
    "ZoneDescription": "Bypassed",
    "PartitionId": "1",
    "ZoneTypeId": ZoneType.SECURITY,
    "CanBeBypassed": 1,
    "ZoneStatus": ZoneStatus.BYPASSED,
}

ZONE_FAULTED = {
    "ZoneDescription": "Faulted",
    "ZoneID": "1",
    "PartitionId": "1",
    "ZoneTypeId": ZoneType.SECURITY,
    "CanBeBypassed": 1,
    "ZoneStatus": ZoneStatus.FAULT,
}

ZONE_TAMPERED = {
    "ZoneDescription": "Tampered",
    "PartitionId": "1",
    "ZoneTypeId": ZoneType.SECURITY,
    "CanBeBypassed": 1,
    "ZoneStatus": ZoneStatus.TROUBLE,
}

ZONE_BYPASSED_LOW_BATTERY = {
    "ZoneDescription": "Bypassed Low Battery",
    "PartitionId": "1",
    "ZoneTypeId": ZoneType.SECURITY,
    "CanBeBypassed": 1,
    "ZoneStatus": 65,
}

ZONE_TROUBLE_LOW_BATTERY = {
    "ZoneDescription": "Trouble Low Battery",
    "PartitionId": "1",
    "ZoneTypeId": ZoneType.SECURITY,
    "CanBeBypassed": 1,
    "ZoneStatus": 72,
}

ZONE_TRIGGERED = {
    "ZoneDescription": "Triggered",
    "PartitionId": "1",
    "ZoneTypeId": ZoneType.SECURITY,
    "CanBeBypassed": 1,
    "ZoneStatus": ZoneStatus.TRIGGERED,
}

ZONE_BUTTON = {
    "ZoneDescription": "Button",
    "PartitionId": "1",
    "ZoneTypeId": ZoneType.SECURITY,
    "CanBeBypassed": 0,
    "ZoneStatus": ZoneStatus.NORMAL,
}

ZONE_SMOKE = {
    "ZoneDescription": "Smoke",
    "PartitionId": "1",
    "ZoneTypeId": ZoneType.FIRE_SMOKE,
    "CanBeBypassed": 0,
    "ZoneStatus": ZoneStatus.NORMAL,
}

ZONE_GAS = {
    "ZoneDescription": "Gas",
    "PartitionId": "1",
    "ZoneTypeId": ZoneType.CARBON_MONOXIDE,
    "CanBeBypassed": 0,
    "ZoneStatus": ZoneStatus.NORMAL,
}


class TestTotalConnectZone(unittest.TestCase):
    """Test TotalConnectZone."""

    def setUp(self):
        """Test setup."""
        self.zone_normal = tcz(ZS_NORMAL, None)
        self.zone_bypassed = tcz(ZONE_BYPASSED, None)
        self.zone_faulted = tcz(ZONE_FAULTED, None)
        self.zone_tampered = tcz(ZONE_TAMPERED, None)
        self.zone_low_battery = tcz(ZONE_LOW_BATTERY, None)
        self.zone_bypassed_low_battery = tcz(ZONE_BYPASSED_LOW_BATTERY, None)
        self.zone_trouble_low_battery = tcz(ZONE_TROUBLE_LOW_BATTERY, None)
        self.zone_triggered = tcz(ZONE_TRIGGERED, None)
        self.zone_button = tcz(ZONE_BUTTON, None)
        self.zone_smoke = tcz(ZONE_SMOKE, None)
        self.zone_gas = tcz(ZONE_GAS, None)
        self.zone_lyric_contact = tcz(ZONE_STATUS_LYRIC_CONTACT, None)
        self.zone_lyric_motion = tcz(ZONE_STATUS_LYRIC_MOTION, None)
        self.zone_lyric_police = tcz(ZONE_STATUS_LYRIC_POLICE, None)
        self.zone_lyric_temp = tcz(ZONE_STATUS_LYRIC_TEMP, None)
        self.zone_lyric_keypad = tcz(ZONE_STATUS_LYRIC_KEYPAD, None)
        self.zone_lyric_local_alarm = tcz(ZONE_STATUS_LYRIC_LOCAL_ALARM, None)

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
        self.zone_lyric_keypad = None
        self.zone_lyric_local_alarm = None

    def tests_normal(self):
        """Normal zone."""
        zone = tcz(ZS_NORMAL, None)
        assert zone.partition == "1"
        assert zone.is_bypassed() is False
        assert zone.is_faulted() is False
        assert zone.is_tampered() is False
        assert zone.is_low_battery() is False
        assert zone.is_troubled() is False
        assert zone.is_triggered() is False

    def tests_update(self):
        """Test updates to a zone."""
        self.assertFalse(self.zone_normal.is_faulted())
        self.zone_normal._update(ZONE_FAULTED)
        self.assertTrue(self.zone_normal.is_faulted())
        self.zone_normal._update(ZS_NORMAL)
        self.assertFalse(self.zone_normal.is_faulted())

        self.assertFalse(self.zone_normal.is_low_battery())
        self.zone_normal._update(ZONE_LOW_BATTERY)
        self.assertTrue(self.zone_normal.is_low_battery())
        self.zone_normal._update(ZS_NORMAL)
        self.assertFalse(self.zone_normal.is_low_battery())

    def tests_update_wrong_zone(self):
        """Test updates to the wrong zone."""
        zone_temp = ZS_NORMAL.copy()
        zone_temp["ZoneID"] = "99"
        with pytest.raises(Exception):
            assert self.zone_normal._update(zone_temp)

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
        self.assertTrue(self.zone_lyric_police.is_type_button())
        self.assertFalse(self.zone_lyric_contact.is_type_button())
        self.assertFalse(self.zone_lyric_local_alarm.is_type_button())
        self.assertFalse(self.zone_lyric_motion.is_type_button())
        self.assertFalse(self.zone_lyric_temp.is_type_button())
        self.assertFalse(self.zone_lyric_keypad.is_type_button())

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
        self.assertFalse(self.zone_lyric_keypad.is_type_security())

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
        self.assertFalse(self.zone_lyric_temp.is_type_fire())

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

    def tests_type_keypad(self):
        """Keypad test."""
        self.assertTrue(self.zone_lyric_keypad.is_type_keypad())
        self.assertFalse(self.zone_lyric_temp.is_type_keypad())

    def tests_type_temperature(self):
        """Temperature test."""
        self.assertFalse(self.zone_lyric_keypad.is_type_temperature())
        self.assertTrue(self.zone_lyric_temp.is_type_temperature())


def test_proa7_zones():
    """Test ProA7."""

    zone_medical = {
        "ZoneDescription": "Gas",
        "PartitionId": "1",
        "ZoneTypeId": ZoneType.PROA7_MEDICAL,
        "CanBeBypassed": 0,
        "ZoneStatus": ZoneStatus.TAMPER,
    }

    zone = tcz(zone_medical, None)
    assert zone.is_type_medical() is True
    assert zone.is_type_button() is True
    assert zone.is_tampered() is True


def test_unknown_type():
    """Test unknown ZoneType."""
    zone_unknown = {
        "ZoneDescription": "Unknown",
        "PartitionId": "1",
        "ZoneTypeId": 12345,
        "CanBeBypassed": 0,
        "ZoneStatus": ZoneStatus.NORMAL,
    }

    zone = tcz(zone_unknown, None)
    assert zone.zone_type_id == 12345
    assert zone._unknown_type_reported is True


def test_unknown_status():
    """Test unknown ZoneStatus."""
    zone_unknown = {
        "ZoneDescription": "Unknown",
        "PartitionId": "1",
        "ZoneTypeId": 12345,
        "CanBeBypassed": 0,
    }

    # invalid status (i.e. None or a string) should raise exception
    with pytest.raises(TotalConnectError):
        tcz(zone_unknown, None)

    # unknown but valid status provided, should not raise
    zone_unknown["ZoneStatus"] = 255
    zone = tcz(zone_unknown, None)
    assert zone.status == 255

def test_bypass():
    """Test bypassing a zone."""
    location = Mock()
    zone_data = {
        "ZoneDescription": "MyZone",
        "PartitionId": "1",
        "ZoneTypeId": ZoneType.SECURITY,
        "CanBeBypassed": 0,
        "ZoneStatus": ZoneStatus.NORMAL,
    }

    # should do nothing if zone cannot be bypassed
    zone = tcz(zone_data, location)
    zone.bypass()
    location.zone_bypass.assert_not_called()

    # now make zone bypassable
    zone_data["CanBeBypassed"] = 1
    zone = tcz(zone_data, location)
    zone.bypass()
    location.zone_bypass.assert_called_once()

