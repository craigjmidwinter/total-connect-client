"""Test client.zone_bypass()."""

import unittest
from unittest.mock import patch

import pytest
from common import create_client
from const import LOCATION_INFO_BASIC_NORMAL

from total_connect_client.const import _ResultCode
from total_connect_client.exceptions import BadResultCodeError

RESPONSE_ZONE_BYPASS_SUCCESS = {
    "ResultCode": _ResultCode.SUCCESS.value,
    "ResultData": "None",
}

# guessing on the response...don't know for sure
RESPONSE_ZONE_BYPASS_FAILURE = {
    "ResultCode": _ResultCode.COMMAND_FAILED.value,
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
        location = self.client.locations[self.location_id]
        zone = location.zones["1"]
        responses = [RESPONSE_ZONE_BYPASS_SUCCESS]
        with patch(
            "total_connect_client.client.TotalConnectClient.request",
            side_effect=responses,
        ):
            # should start not bypassed
            assert zone.is_bypassed() is False

            # now bypass the zone
            location.zone_bypass("1")

            # should now be bypassed
            assert zone.is_bypassed() is True

    def tests_zone_bypass_failure(self):
        """Test Zone Bypass with a normal response."""
        location = self.client.locations[self.location_id]
        zone = location.zones["1"]
        responses = [RESPONSE_ZONE_BYPASS_FAILURE]
        with patch(
            "total_connect_client.client.TotalConnectClient.request",
            side_effect=responses,
        ):
            # should start not bypassed
            assert zone.is_bypassed() is False

            # try to bypass the zone
            with pytest.raises(BadResultCodeError):
                location.zone_bypass("1")

            # should not be bypassed
            assert zone.is_bypassed() is False
