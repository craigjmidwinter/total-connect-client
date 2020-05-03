"""Test total_connect_client."""

import unittest

import TotalConnectClient
from TotalConnectClient import TotalConnectLocation as tcl

from const import LOCATION_INFO_BASIC_NORMAL, PASSWORD_BAD, USERNAME_BAD

ZONE_NORMAL = {
    "PartitionId": "1",
    "Batterylevel": "-1",
    "Signalstrength": "-1",
    "zoneAdditionalInfo": None,
    "ZoneID": "1",
    "ZoneStatus": TotalConnectClient.ZONE_STATUS_NORMAL,
    "ZoneTypeId": TotalConnectClient.ZONE_TYPE_SECURITY,
    "CanBeBypassed": 1,
    "ZoneFlags": None,
}

ZONE_STATUS_INFO = []
ZONE_STATUS_INFO.append(ZONE_NORMAL)

ZONES = {"ZoneStatusInfoWithPartitionId": ZONE_STATUS_INFO}

ZONE_STATUS = {"Zones": ZONES}

RESULT_SUCCESS = {"ResultCode": 0, "ResultData": "Success", "ZoneStatus": ZONE_STATUS}

RESULT_NOT_SUPPORTED = {"ResultCode": -120, "ResultData": "Not Supported"}

RESULT_UNKNOWN = {"ResultCode": 999, "ResultData": "Unknown"}


class FakeGoodClient(TotalConnectClient.TotalConnectClient):
    """Fake total connect client."""

    def authenticate(self):
        """Pretend to authenticate."""
        self.token = True
        self._valid_credentials = True
        self.populate_details()

    def populate_details(self):
        """Populate system details."""
        self.locations[LOCATION_INFO_BASIC_NORMAL["LocationID"]] = tcl(
            LOCATION_INFO_BASIC_NORMAL, self
        )
        self._result = RESULT_SUCCESS

    def request(self, new_request):
        """Fake a request."""
        return self._result

    def logout(self):
        """Pretend to logout."""
        if self.is_logged_in():
            self.token = False
            return True

        return False


class TestTotalConnectClient(unittest.TestCase):
    """Test TotalConnectClient."""

    def setUp(self):
        """Test setup."""
        self.client = FakeGoodClient(USERNAME_BAD, PASSWORD_BAD)
        self.location_id = LOCATION_INFO_BASIC_NORMAL["LocationID"]

    def tearDown(self):
        """Test cleanup."""
        self.client = None

    def tests_get_zone_details(self):
        """Test get_zone_details()."""
        self.client._result = RESULT_SUCCESS
        self.assertTrue(self.client.get_zone_details(self.location_id))
        self.client._result = RESULT_NOT_SUPPORTED
        self.assertFalse(self.client.get_zone_details(self.location_id))
        self.client._result = RESULT_UNKNOWN
        self.assertFalse(self.client.get_zone_details(self.location_id))
