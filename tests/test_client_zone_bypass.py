"""Test client.zone_bypass()."""

from unittest.mock import patch
import unittest
import pytest

from client import TotalConnectClient
from common import create_client
from const import LOCATION_INFO_BASIC_NORMAL
from exceptions import BadResultCodeError

RESPONSE_ZONE_BYPASS_SUCCESS = {
    "ResultCode": TotalConnectClient.SUCCESS,
    "ResultData": "None",
}

# guessing on the response...don't know for sure
RESPONSE_ZONE_BYPASS_FAILURE = {
    "ResultCode": TotalConnectClient.COMMAND_FAILED,
    "ResultData": "None",
}


class TestTotalConnectClient(unittest.TestCase):
    """Test TotalConnectClient."""

    def setUp(self):
        """Test setup."""
        self.client = create_client()
        self.location_id = LOCATION_INFO_BASIC_NORMAL["LocationID"]

    def tearDown(self):
        """Test cleanup."""
        self.client = None

    def tests_zone_bypass_success(self):
        """Test Zone Bypass with a normal response."""
        zone = self.client.locations[self.location_id].zones["1"]
        responses = [RESPONSE_ZONE_BYPASS_SUCCESS]
        with patch("client.TotalConnectClient.request", side_effect=responses):
            # should start not bypassed
            assert zone.is_bypassed() is False

            # now bypass the zone
            self.client.zone_bypass("1", self.location_id)

            # should now be bypassed
            assert zone.is_bypassed() is True

    def tests_zone_bypass_failure(self):
        """Test Zone Bypass with a normal response."""
        zone = self.client.locations[self.location_id].zones["1"]
        responses = [RESPONSE_ZONE_BYPASS_FAILURE]
        with patch("client.TotalConnectClient.request", side_effect=responses):
            # should start not bypassed
            assert zone.is_bypassed() is False

            # try to bypass the zone
            with pytest.raises(BadResultCodeError):
                self.client.zone_bypass("1", self.location_id)

            # should not be bypassed
            assert zone.is_bypassed() is False
