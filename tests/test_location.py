"""Tests TotalConnectLocation."""

from unittest.mock import Mock 
from total_connect_client.location import TotalConnectLocation

from const import LOCATION_INFO_BASIC_NORMAL

def tests_location_basic():
    """Tests basic location info."""
    location = TotalConnectLocation(LOCATION_INFO_BASIC_NORMAL, Mock())
    location.location_id = 123456
