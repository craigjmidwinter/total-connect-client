"""Test total_connect_client."""

import unittest
from unittest.mock import Mock, patch

from const import PASSWORD_BAD, USERNAME_BAD
from TotalConnectClient import TotalConnectClient as tcc


class FakeClient(tcc):
    """Fake total connect client."""

    def authenticate(self):
        """Pretend to authenticate."""
        self.token = True
        self._valid_credentials = True


class TestTotalConnectClient(unittest.TestCase):
    """Test TotalConnectClient."""

    def setUp(self):
        """Test setup."""
        self.location_id = "123456"
        self.client = FakeClient(USERNAME_BAD, PASSWORD_BAD)
        self.client.locations[self.location_id] = Mock()
        self.client.locations[self.location_id].security_device_id = "987654"

        self.response = {"ResultCode": -1, "ResultData": "test"}

    def tearDown(self):
        """Test cleanup."""
        self.client = None

    def tests_arm(self):
        """Test arm."""
        with patch.object(FakeClient, "request", return_value=self.response):

            # Test with all zones closed - expecting ARM_SUCCESS
            self.response["ResultCode"] = tcc.ARM_SUCCESS
            self.assertTrue(self.client.arm_away(self.location_id))
            self.assertTrue(self.client.arm_away_instant(self.location_id))
            self.assertTrue(self.client.arm_stay(self.location_id))
            self.assertTrue(self.client.arm_stay_instant(self.location_id))
            self.assertTrue(self.client.arm_stay_night(self.location_id))

            # Test with a zone faulted - expecting COMMAND_FAILED
            self.response["ResultCode"] = tcc.COMMAND_FAILED
            self.assertFalse(self.client.arm_away(self.location_id))
            self.assertFalse(self.client.arm_away_instant(self.location_id))
            self.assertFalse(self.client.arm_stay(self.location_id))
            self.assertFalse(self.client.arm_stay_instant(self.location_id))
            self.assertFalse(self.client.arm_stay_night(self.location_id))

            # What about trying to arm after already armed?
            # What result will TC give?

    def tests_disarm(self):
        """Test disarm."""
        with patch.object(FakeClient, "request", return_value=self.response):

            # Test with all zones closed - expecting DISARM_SUCCESS
            self.response["ResultCode"] = tcc.DISARM_SUCCESS
            self.assertTrue(self.client.disarm(self.location_id))

            # Test with a problem.
            # Don't know what a failed response would be...using COMMAND_FAILED
            self.response["ResultCode"] = tcc.COMMAND_FAILED
            self.assertFalse(self.client.disarm(self.location_id))

            # Test trying to disarm after already disarmed
            # Did this once on my Lynx 7000 and it gave result code SUCCESS
            self.response["ResultCode"] = tcc.SUCCESS
            self.assertTrue(self.client.disarm(self.location_id))
