"""Tests TotalConnectLocation."""

from unittest.mock import Mock

from const import (
    LOCATION_ID,
    RESPONSE_UNKNOWN,
    REST_RESULT_FULL_STATUS,
    REST_RESULT_PARTITIONS_CONFIG,
    REST_RESULT_PARTITIONS_ZONES,
    REST_RESULT_SESSION_DETAILS,
    REST_RESULT_VALIDATE_USER_LOCATIONS,
)
from pytest import raises

from total_connect_client.const import ArmingState
from total_connect_client.exceptions import (
    FeatureNotSupportedError,
    PartialResponseError,
    TotalConnectError,
)
from total_connect_client.location import TotalConnectLocation

result_location = REST_RESULT_SESSION_DETAILS["SessionDetailsResult"]["Locations"][0]
result_num_zones = len(REST_RESULT_PARTITIONS_ZONES["ZoneStatus"]["Zones"])


def tests_location_basic():
    """Tests basic location info."""
    location = TotalConnectLocation(result_location, Mock())
    assert location.location_id == LOCATION_ID
    assert location.is_ac_loss() is False
    assert location.is_cover_tampered() is False
    assert location.is_low_battery() is False


def tests_get_partition_details():
    """Test get_partition_details function."""

    client = Mock()
    location = TotalConnectLocation(result_location, client)
    assert len(location.partitions) == 0

    # first an error
    client.http_request.return_value = RESPONSE_UNKNOWN
    client.raise_for_resultcode.side_effect = TotalConnectError()
    with raises(TotalConnectError):
        location.get_partition_details()
    assert len(location.partitions) == 0

    # now with partial data
    client.http_request.return_value = {}
    client.raise_for_resultcode.side_effect = None
    with raises(PartialResponseError):
        location.get_partition_details()
    assert len(location.partitions) == 0

    # now it works
    client.http_request.return_value = REST_RESULT_PARTITIONS_CONFIG
    location.get_partition_details()
    assert len(location.partitions) == 1


def tests_get_zone_details():
    """Test get_zone_details function."""

    client = Mock()
    client.http_request.return_value = REST_RESULT_PARTITIONS_ZONES
    client.raise_for_resultcode.return_value = None

    location = TotalConnectLocation(result_location, client)
    assert len(location.zones) == 0

    # first an error
    client.raise_for_resultcode.side_effect = FeatureNotSupportedError()
    location.get_zone_details()
    assert len(location.zones) == 0

    # now it should work
    client.raise_for_resultcode.side_effect = None
    location.get_zone_details()
    assert len(location.zones) == result_num_zones


def tests_get_panel_metadata():
    """Test status updates."""

    client = Mock()
    client.http_request.return_value = REST_RESULT_PARTITIONS_ZONES
    client.raise_for_resultcode.return_value = None

    location = TotalConnectLocation(result_location, client)
    location.get_zone_details()
    assert len(location.zones) == result_num_zones
    assert location.arming_state == ArmingState.UNKNOWN

    client.http_request.return_value = REST_RESULT_FULL_STATUS
    location.get_panel_meta_data()
    assert location.arming_state == ArmingState.DISARMED_ZONE_FAULTED


def tests_usercode():
    """Test usercode fuctions."""
    client = Mock()
    location = TotalConnectLocation(result_location, client)

    # first an error
    client.http_request.return_value = RESPONSE_UNKNOWN
    client.raise_for_resultcode.side_effect = TotalConnectError()
    assert location.set_usercode("1234") is False

    client.raise_for_resultcode.side_effect = None
    client.http_request.return_value = REST_RESULT_VALIDATE_USER_LOCATIONS
    assert location.set_usercode("1234") is True


def tests_partition_list():
    """Test _build_partition_list."""
    client = Mock()
    location = TotalConnectLocation(result_location, client)
    # if we pass 1 it should be [1]
    assert location._build_partition_list(1) == [1]
    # if we pass nothing, it should be [1] because that's the only partition
    assert location._build_partition_list() == [1]
    # invalid partition_id should raise exception
    with raises(TotalConnectError):
        assert location._build_partition_list(999)
