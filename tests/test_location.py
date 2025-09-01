"""Tests TotalConnectLocation."""

from unittest.mock import Mock
import requests_mock
from common import create_http_client
from const import (
    LOCATION_ID,
    RESPONSE_UNKNOWN,
    REST_RESULT_FULL_STATUS,
    REST_RESULT_PARTITIONS_CONFIG,
    REST_RESULT_PARTITIONS_ZONES,
    REST_RESULT_SESSION_DETAILS,
    REST_RESULT_VALIDATE_USER_LOCATIONS,
    PANEL_STATUS_DISARMED,
    PANEL_STATUS_ARMED_AWAY,
    RESPONSE_DISARM_SUCCESS,
)
from pytest import raises

from total_connect_client.const import ArmingState, ArmType
from total_connect_client.exceptions import (
    FeatureNotSupportedError,
    PartialResponseError,
    TotalConnectError,
)
from total_connect_client.location import TotalConnectLocation
from total_connect_client.const import make_http_endpoint

RESULT_LOCATION = REST_RESULT_SESSION_DETAILS["SessionDetailsResult"]["Locations"][0]
result_num_zones = len(REST_RESULT_PARTITIONS_ZONES["ZoneStatus"]["Zones"])


def tests_location_basic():
    """Tests basic location info."""
    location = TotalConnectLocation(RESULT_LOCATION, Mock())
    assert location.location_id == LOCATION_ID
    assert location.is_ac_loss() is False
    assert location.is_cover_tampered() is False
    assert location.is_low_battery() is False


def tests_get_partition_details():
    """Test get_partition_details function."""

    client = Mock()
    location = TotalConnectLocation(RESULT_LOCATION, client)
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

    location = TotalConnectLocation(RESULT_LOCATION, client)
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

    location = TotalConnectLocation(RESULT_LOCATION, client)
    location.get_zone_details()
    assert len(location.zones) == result_num_zones
    assert location.arming_state == ArmingState.UNKNOWN

    client.http_request.return_value = REST_RESULT_FULL_STATUS
    location.get_panel_meta_data()
    assert location.arming_state == ArmingState.DISARMED_ZONE_FAULTED


def tests_usercode():
    """Test usercode fuctions."""
    client = Mock()
    location = TotalConnectLocation(RESULT_LOCATION, client)

    # first an error
    client.http_request.return_value = RESPONSE_UNKNOWN
    client.raise_for_resultcode.side_effect = TotalConnectError()
    assert location.set_usercode("1234") is False

    client.raise_for_resultcode.side_effect = None
    client.http_request.return_value = REST_RESULT_VALIDATE_USER_LOCATIONS
    assert location.set_usercode("1234") is True


def tests_disarm():
    """Test disarm."""
    client = create_http_client(PANEL_STATUS_ARMED_AWAY)
    location = client.locations[LOCATION_ID]
    assert location.arming_state.is_armed()

    with requests_mock.Mocker() as rm:
        rm.put(
            make_http_endpoint(
                f"api/v3/locations/{location.location_id}/devices/{location.security_device_id}/partitions/disArm"
            ),
            json=RESPONSE_DISARM_SUCCESS,
        )

        # try to disarm a non-existent partition
        with raises(TotalConnectError):
            location.disarm(999, "1234")

        # now should work
        location.disarm(1, "1234")

        rm.get(
            make_http_endpoint(
                f"api/v3/locations/{location.location_id}/partitions/fullStatus"
            ),
            json=PANEL_STATUS_DISARMED,
        )
        location.get_panel_meta_data()
        assert location.arming_state.is_disarmed()

        # now should do nothing because already disarmed
        location.disarm(1, "1234")
        assert location.arming_state.is_disarmed()

        # now try just the location
        rm.get(
            make_http_endpoint(
                f"api/v3/locations/{location.location_id}/partitions/fullStatus"
            ),
            json=PANEL_STATUS_ARMED_AWAY,
        )
        location.get_panel_meta_data()
        assert location.arming_state.is_armed()

        rm.put(
            make_http_endpoint(
                f"api/v3/locations/{location.location_id}/devices/{location.security_device_id}/partitions/disArm"
            ),
            json=RESPONSE_DISARM_SUCCESS,
        )
        location.disarm(usercode="1234")

        rm.get(
            make_http_endpoint(
                f"api/v3/locations/{location.location_id}/partitions/fullStatus"
            ),
            json=PANEL_STATUS_DISARMED,
        )
        location.get_panel_meta_data()
        assert location.arming_state.is_disarmed()

        # now should do nothing because already disarmed
        location.disarm(usercode="1234")
        assert location.arming_state.is_disarmed()


def tests_arm():
    """Test arm."""
    client = create_http_client(PANEL_STATUS_DISARMED)
    location = client.locations[LOCATION_ID]
    assert location.arming_state.is_disarmed()

    with requests_mock.Mocker() as rm:
        rm.put(
            make_http_endpoint(
                f"api/v3/locations/{location.location_id}/devices/{location.security_device_id}/partitions/arm"
            ),
            json=RESPONSE_DISARM_SUCCESS,
        )

        # try to arm a non-existent partition
        with raises(TotalConnectError):
            location.arm(partition_id=999, usercode="1234", arm_type=ArmType.AWAY)

        # now should work
        location.arm(partition_id=1, usercode="1234", arm_type=ArmType.AWAY)

        # now just the location should work
        location.arm(usercode="1234", arm_type=ArmType.AWAY)
