"""Tests TotalConnectLocation."""

from unittest.mock import Mock
from urllib.parse import parse_qs

import requests_mock
from common import create_http_client
from const import (
    LOCATION_ID,
    PANEL_STATUS_ARMED_AWAY,
    PANEL_STATUS_DISARMED,
    RESPONSE_DISARM_SUCCESS,
    RESPONSE_UNKNOWN,
    REST_RESULT_FULL_STATUS,
    REST_RESULT_PARTITIONS_CONFIG,
    REST_RESULT_PARTITIONS_ZONES,
    REST_RESULT_SECURITY_SYNCHRONIZE,
    REST_RESULT_SESSION_DETAILS,
    REST_RESULT_VALIDATE_USER_LOCATIONS,
    panel_with_status,
)
from pytest import raises

from total_connect_client.client import ArmingHelper
from total_connect_client.const import ArmingState, ArmType, _ResultCode, make_http_endpoint
from total_connect_client.exceptions import (
    FailedToBypassZone,
    FeatureNotSupportedError,
    PartialResponseError,
    TotalConnectError,
    UsercodeInvalid,
    UsercodeUnavailable,
)
from total_connect_client.location import TotalConnectLocation
from total_connect_client.zone import TotalConnectZone, ZoneStatus

RESULT_LOCATION = REST_RESULT_SESSION_DETAILS["SessionDetailsResult"]["Locations"][0]
result_num_zones = len(REST_RESULT_PARTITIONS_ZONES["ZoneStatus"]["Zones"])


def _sent_form(rm):
    """Return the last request's form-encoded body as a flat dict of first values."""
    return {k: v[0] for k, v in parse_qs(rm.last_request.text).items()}


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
            make_http_endpoint(f"api/v3/locations/{location.location_id}/partitions/fullStatus"),
            json=PANEL_STATUS_DISARMED,
        )
        location.get_panel_meta_data()
        assert location.arming_state.is_disarmed()

        # now should do nothing because already disarmed
        location.disarm(1, "1234")
        assert location.arming_state.is_disarmed()

        # now try just the location
        rm.get(
            make_http_endpoint(f"api/v3/locations/{location.location_id}/partitions/fullStatus"),
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
            make_http_endpoint(f"api/v3/locations/{location.location_id}/partitions/fullStatus"),
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


def test_arm_away_sends_arm_type_and_usercode_then_panel_reports_armed_away():
    """arm(ArmType.AWAY) sends armType=AWAY and the usercode, and a subsequent panel
    refresh shows the location armed away -- the README's 'Arming (away)' claim."""
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
        location.arm(arm_type=ArmType.AWAY, usercode="1234")

        sent = _sent_form(rm)
        assert sent["armType"] == str(ArmType.AWAY.value)
        assert sent["userCode"] == "1234"

        rm.get(
            make_http_endpoint(f"api/v3/locations/{location.location_id}/partitions/fullStatus"),
            json=PANEL_STATUS_ARMED_AWAY,
        )
        location.get_panel_meta_data()
        assert location.arming_state.is_armed_away()


def test_arm_stay_sends_arm_type_and_usercode_then_panel_reports_armed_stay():
    """arm(ArmType.STAY) sends armType=STAY and a subsequent panel refresh shows the
    location armed home -- the README's 'Arming (stay)' claim."""
    client = create_http_client(PANEL_STATUS_DISARMED)
    location = client.locations[LOCATION_ID]

    with requests_mock.Mocker() as rm:
        rm.put(
            make_http_endpoint(
                f"api/v3/locations/{location.location_id}/devices/{location.security_device_id}/partitions/arm"
            ),
            json=RESPONSE_DISARM_SUCCESS,
        )
        location.arm(arm_type=ArmType.STAY, usercode="1234")

        sent = _sent_form(rm)
        assert sent["armType"] == str(ArmType.STAY.value)

        rm.get(
            make_http_endpoint(f"api/v3/locations/{location.location_id}/partitions/fullStatus"),
            json=panel_with_status(ArmingState.ARMED_STAY),
        )
        location.get_panel_meta_data()
        assert location.arming_state.is_armed_home()


def test_arm_stay_night_sends_arm_type_and_usercode_then_panel_reports_armed_night():
    """arm(ArmType.STAY_NIGHT) sends armType=STAY_NIGHT and a subsequent panel refresh
    shows the location armed night -- the README's 'Arming (night)' claim."""
    client = create_http_client(PANEL_STATUS_DISARMED)
    location = client.locations[LOCATION_ID]

    with requests_mock.Mocker() as rm:
        rm.put(
            make_http_endpoint(
                f"api/v3/locations/{location.location_id}/devices/{location.security_device_id}/partitions/arm"
            ),
            json=RESPONSE_DISARM_SUCCESS,
        )
        location.arm(arm_type=ArmType.STAY_NIGHT, usercode="1234")

        sent = _sent_form(rm)
        assert sent["armType"] == str(ArmType.STAY_NIGHT.value)

        rm.get(
            make_http_endpoint(f"api/v3/locations/{location.location_id}/partitions/fullStatus"),
            json=panel_with_status(ArmingState.ARMED_STAY_NIGHT),
        )
        location.get_panel_meta_data()
        assert location.arming_state.is_armed_night()


def test_arming_helper_arm_stay_instant_sends_stay_instant_arm_type():
    """ArmingHelper.arm_stay_instant() sends armType=STAY_INSTANT via location.arm()."""
    client = create_http_client(PANEL_STATUS_DISARMED)
    location = client.locations[LOCATION_ID]

    with requests_mock.Mocker() as rm:
        rm.put(
            make_http_endpoint(
                f"api/v3/locations/{location.location_id}/devices/{location.security_device_id}/partitions/arm"
            ),
            json=RESPONSE_DISARM_SUCCESS,
        )
        ArmingHelper(location).arm_stay_instant(usercode="1234")
        sent = _sent_form(rm)
        assert sent["armType"] == str(ArmType.STAY_INSTANT.value)


def test_arming_helper_arm_away_instant_sends_away_instant_arm_type():
    """ArmingHelper.arm_away_instant() sends armType=AWAY_INSTANT via location.arm()."""
    client = create_http_client(PANEL_STATUS_DISARMED)
    location = client.locations[LOCATION_ID]

    with requests_mock.Mocker() as rm:
        rm.put(
            make_http_endpoint(
                f"api/v3/locations/{location.location_id}/devices/{location.security_device_id}/partitions/arm"
            ),
            json=RESPONSE_DISARM_SUCCESS,
        )
        ArmingHelper(location).arm_away_instant(usercode="1234")
        sent = _sent_form(rm)
        assert sent["armType"] == str(ArmType.AWAY_INSTANT.value)


def test_arm_with_invalid_usercode_raises_usercode_invalid():
    """Arming with a usercode the panel rejects raises UsercodeInvalid."""
    client = create_http_client(PANEL_STATUS_DISARMED)
    location = client.locations[LOCATION_ID]

    with requests_mock.Mocker() as rm:
        rm.put(
            make_http_endpoint(
                f"api/v3/locations/{location.location_id}/devices/{location.security_device_id}/partitions/arm"
            ),
            json={"ResultCode": _ResultCode.USER_CODE_INVALID.value, "ResultData": "bad code"},
        )
        with raises(UsercodeInvalid):
            location.arm(arm_type=ArmType.AWAY, usercode="0000")


def test_arm_with_unavailable_usercode_raises_usercode_unavailable():
    """Arming with a usercode the panel does not recognize raises UsercodeUnavailable."""
    client = create_http_client(PANEL_STATUS_DISARMED)
    location = client.locations[LOCATION_ID]

    with requests_mock.Mocker() as rm:
        rm.put(
            make_http_endpoint(
                f"api/v3/locations/{location.location_id}/devices/{location.security_device_id}/partitions/arm"
            ),
            json={"ResultCode": _ResultCode.USER_CODE_UNAVAILABLE.value, "ResultData": "no code"},
        )
        with raises(UsercodeUnavailable):
            location.arm(arm_type=ArmType.AWAY, usercode="0000")


def test_arm_command_failed_logs_warning_and_raises(caplog):
    """A COMMAND_FAILED response (e.g. a faulted zone blocking arming) logs a helpful
    warning and still raises, rather than silently doing nothing."""
    client = create_http_client(PANEL_STATUS_DISARMED)
    location = client.locations[LOCATION_ID]

    with requests_mock.Mocker() as rm:
        rm.put(
            make_http_endpoint(
                f"api/v3/locations/{location.location_id}/devices/{location.security_device_id}/partitions/arm"
            ),
            json={"ResultCode": _ResultCode.COMMAND_FAILED.value, "ResultData": "blocked"},
        )
        with raises(TotalConnectError):
            location.arm(arm_type=ArmType.AWAY, usercode="1234")
        assert "could not arm system" in caplog.text


def test_disarm_with_invalid_usercode_raises_usercode_invalid():
    """Disarming with a usercode the panel rejects raises UsercodeInvalid."""
    client = create_http_client(PANEL_STATUS_ARMED_AWAY)
    location = client.locations[LOCATION_ID]

    with requests_mock.Mocker() as rm:
        rm.put(
            make_http_endpoint(
                f"api/v3/locations/{location.location_id}/devices/{location.security_device_id}/partitions/disArm"
            ),
            json={"ResultCode": _ResultCode.USER_CODE_INVALID.value, "ResultData": "bad code"},
        )
        with raises(UsercodeInvalid):
            location.disarm(usercode="0000")


def test_disarm_with_unavailable_usercode_raises_usercode_unavailable():
    """Disarming with a usercode the panel does not recognize raises UsercodeUnavailable."""
    client = create_http_client(PANEL_STATUS_ARMED_AWAY)
    location = client.locations[LOCATION_ID]

    with requests_mock.Mocker() as rm:
        rm.put(
            make_http_endpoint(
                f"api/v3/locations/{location.location_id}/devices/{location.security_device_id}/partitions/disArm"
            ),
            json={"ResultCode": _ResultCode.USER_CODE_UNAVAILABLE.value, "ResultData": "no code"},
        )
        with raises(UsercodeUnavailable):
            location.disarm(usercode="0000")


def test_get_panel_meta_data_raises_partial_response_error_when_panel_status_missing():
    """A response missing the PanelStatus section is treated as a partial/retryable
    response, not silently accepted -- protects the 'getting panel status' claim."""
    client = Mock()
    client.raise_for_resultcode.return_value = None
    location = TotalConnectLocation(RESULT_LOCATION, client)
    client.http_request.return_value = {"ArmingState": ArmingState.DISARMED.value}
    with raises(PartialResponseError):
        location.get_panel_meta_data()


def test_get_panel_meta_data_raises_partial_response_error_when_arming_state_missing():
    """A response missing ArmingState is treated as a partial/retryable response."""
    client = Mock()
    client.raise_for_resultcode.return_value = None
    location = TotalConnectLocation(RESULT_LOCATION, client)
    client.http_request.return_value = {
        "PanelStatus": {
            "IsInACLoss": False,
            "IsInLowBattery": False,
            "IsCoverTampered": False,
            "Partitions": [],
            "Zones": [],
        }
    }
    with raises(PartialResponseError):
        location.get_panel_meta_data()


def test_get_panel_meta_data_raises_total_connect_error_for_unknown_arming_state():
    """An ArmingState value not in the known enum raises rather than being silently
    accepted as some default state."""
    client = Mock()
    client.raise_for_resultcode.return_value = None
    location = TotalConnectLocation(RESULT_LOCATION, client)
    client.http_request.return_value = {
        "PanelStatus": {
            "IsInACLoss": False,
            "IsInLowBattery": False,
            "IsCoverTampered": False,
            "Partitions": [],
            "Zones": [],
        },
        "ArmingState": 999999999,
    }
    with raises(TotalConnectError):
        location.get_panel_meta_data()


def test_get_panel_meta_data_raises_partial_response_error_when_partition_id_missing():
    """A partition update missing PartitionID is treated as a partial response."""
    client = Mock()
    client.raise_for_resultcode.return_value = None
    location = TotalConnectLocation(RESULT_LOCATION, client)
    client.http_request.return_value = {
        "PanelStatus": {
            "IsInACLoss": False,
            "IsInLowBattery": False,
            "IsCoverTampered": False,
            "Partitions": [{"ArmingState": ArmingState.DISARMED.value}],
            "Zones": [{"ZoneID": 1, "ZoneDescription": "x", "ZoneStatus": 0}],
        },
        "ArmingState": ArmingState.DISARMED.value,
    }
    with raises(PartialResponseError):
        location.get_panel_meta_data()


def test_get_panel_meta_data_raises_total_connect_error_when_zones_empty():
    """An empty Zones list means the panel needs a sync -- this is surfaced as an
    error rather than silently leaving stale/no zone data -- protects the
    'getting zone status' claim."""
    client = Mock()
    client.raise_for_resultcode.return_value = None
    location = TotalConnectLocation(RESULT_LOCATION, client)
    client.http_request.return_value = {
        "PanelStatus": {
            "IsInACLoss": False,
            "IsInLowBattery": False,
            "IsCoverTampered": False,
            "Partitions": [],
            "Zones": [],
        },
        "ArmingState": ArmingState.DISARMED.value,
    }
    with raises(TotalConnectError):
        location.get_panel_meta_data()


def test_get_zone_details_warns_and_leaves_zones_empty_when_none_found():
    """No zones in a ZoneStatus response is logged and does not raise (panel likely
    needs a sync via the app), matching _update_zone_details's documented behavior."""
    client = Mock()
    client.raise_for_resultcode.return_value = None
    location = TotalConnectLocation(RESULT_LOCATION, client)
    client.http_request.return_value = {"ZoneStatus": {"Zones": None}}
    location.get_zone_details()
    assert len(location.zones) == 0


def test_zone_status_reflects_bypassed_zone_from_panel_meta_data():
    """zone_status() reflects a zone the panel reports as bypassed after a refresh --
    'getting zone status (normal, fault, ... etc)'."""
    client = create_http_client(PANEL_STATUS_DISARMED)
    location = client.locations[LOCATION_ID]

    with requests_mock.Mocker() as rm:
        rm.get(
            make_http_endpoint(f"api/v3/locations/{location.location_id}/partitions/fullStatus"),
            json=REST_RESULT_FULL_STATUS,
        )
        location.get_panel_meta_data()

    # zone 8 in REST_RESULT_FULL_STATUS has ZoneStatus 1 (bypassed)
    assert location.zone_status(8) == ZoneStatus.BYPASSED
    assert location.zones[8].is_bypassed() is True


def test_zone_status_raises_for_unknown_zone():
    """zone_status() raises for a zone ID that does not exist at this location."""
    location = TotalConnectLocation(RESULT_LOCATION, Mock())
    with raises(TotalConnectError):
        location.zone_status(999)


def test_zone_bypass_sends_zone_id_and_usercode():
    """zone_bypass() sends the zone ID and the location's usercode to the bypass endpoint."""
    client = Mock()
    client.raise_for_resultcode.return_value = None
    client.http_request.return_value = {"ResultCode": 0, "ResultData": "Success"}
    location = TotalConnectLocation(RESULT_LOCATION, client)
    location.usercode = "1234"
    zone = TotalConnectZone(
        {
            "ZoneID": 1,
            "ZoneDescription": "Front Door",
            "ZoneStatus": ZoneStatus.FAULT,
            "CanBeBypassed": 1,
            "PartitionId": 1,
        },
        location,
    )
    location.zones = {1: zone}

    location.zone_bypass(1)

    kwargs = client.http_request.call_args.kwargs
    assert kwargs["data"]["ZoneIds"] == [1]
    assert kwargs["data"]["UserCode"] == 1234


def test_zone_bypass_all_only_bypasses_faulted_zones_that_allow_it():
    """zone_bypass_all() bypasses faulted+bypassable zones and skips faulted zones
    that cannot be bypassed and zones that are not faulted."""
    client = Mock()
    client.raise_for_resultcode.return_value = None
    client.http_request.return_value = {"ResultCode": 0, "ResultData": "Success"}
    location = TotalConnectLocation(RESULT_LOCATION, client)

    faulted_bypassable = TotalConnectZone(
        {
            "ZoneID": 1,
            "ZoneDescription": "a",
            "ZoneStatus": ZoneStatus.FAULT,
            "CanBeBypassed": 1,
            "PartitionId": 1,
        },
        location,
    )
    faulted_not_bypassable = TotalConnectZone(
        {
            "ZoneID": 2,
            "ZoneDescription": "b",
            "ZoneStatus": ZoneStatus.FAULT,
            "CanBeBypassed": 0,
            "PartitionId": 1,
        },
        location,
    )
    normal_zone = TotalConnectZone(
        {
            "ZoneID": 3,
            "ZoneDescription": "c",
            "ZoneStatus": ZoneStatus.NORMAL,
            "CanBeBypassed": 1,
            "PartitionId": 1,
        },
        location,
    )
    location.zones = {1: faulted_bypassable, 2: faulted_not_bypassable, 3: normal_zone}

    location.zone_bypass_all()

    kwargs = client.http_request.call_args.kwargs
    assert kwargs["data"]["ZoneIds"] == [1]


def test_zone_bypass_all_does_nothing_when_no_zones_are_faulted():
    """zone_bypass_all() makes no HTTP request when there is nothing to bypass."""
    client = Mock()
    location = TotalConnectLocation(RESULT_LOCATION, client)
    location.zones = {}
    location.zone_bypass_all()
    client.http_request.assert_not_called()


def test_bypass_unknown_zone_id_is_skipped_without_error():
    """Bypassing a zone ID that does not exist at this location is a no-op, not an error."""
    client = Mock()
    location = TotalConnectLocation(RESULT_LOCATION, client)
    location.zone_bypass(999)
    client.http_request.assert_not_called()


def test_bypass_zone_that_cannot_be_bypassed_is_skipped():
    """Bypassing a zone flagged CanBeBypassed=0 is a no-op, not an error."""
    client = Mock()
    location = TotalConnectLocation(RESULT_LOCATION, client)
    zone = TotalConnectZone(
        {
            "ZoneID": 1,
            "ZoneDescription": "x",
            "ZoneStatus": ZoneStatus.FAULT,
            "CanBeBypassed": 0,
            "PartitionId": 1,
        },
        location,
    )
    location.zones = {1: zone}
    location.zone_bypass(1)
    client.http_request.assert_not_called()


def test_bypass_raises_failed_to_bypass_zone_when_api_reports_failure():
    """A FAILED_TO_BYPASS_ZONE ResultCode from the bypass endpoint raises FailedToBypassZone."""
    client = Mock()
    client.raise_for_resultcode.return_value = None
    client.http_request.return_value = {
        "ResultCode": _ResultCode.FAILED_TO_BYPASS_ZONE.value,
        "ResultData": "nope",
    }
    location = TotalConnectLocation(RESULT_LOCATION, client)
    zone = TotalConnectZone(
        {
            "ZoneID": 1,
            "ZoneDescription": "x",
            "ZoneStatus": ZoneStatus.FAULT,
            "CanBeBypassed": 1,
            "PartitionId": 1,
        },
        location,
    )
    location.zones = {1: zone}
    with raises(FailedToBypassZone):
        location.zone_bypass(1)


def test_clear_bypass_does_nothing_when_no_zones_bypassed():
    """clear_bypass() makes no HTTP request when nothing is bypassed."""
    client = Mock()
    location = TotalConnectLocation(RESULT_LOCATION, client)
    zone = TotalConnectZone(
        {
            "ZoneID": 1,
            "ZoneDescription": "x",
            "ZoneStatus": ZoneStatus.NORMAL,
            "CanBeBypassed": 1,
            "PartitionId": 1,
        },
        location,
    )
    location.zones = {1: zone}
    location.clear_bypass()
    client.http_request.assert_not_called()


def test_clear_bypass_sends_usercode_when_zones_are_bypassed():
    """clear_bypass() sends the location's usercode to the clearBypass endpoint when
    at least one zone is bypassed."""
    client = Mock()
    client.raise_for_resultcode.return_value = None
    client.http_request.return_value = {"ResultCode": 0, "ResultData": "Success"}
    location = TotalConnectLocation(RESULT_LOCATION, client)
    location.usercode = "1234"
    zone = TotalConnectZone(
        {
            "ZoneID": 1,
            "ZoneDescription": "x",
            "ZoneStatus": ZoneStatus.BYPASSED,
            "CanBeBypassed": 1,
            "PartitionId": 1,
        },
        location,
    )
    location.zones = {1: zone}

    location.clear_bypass()

    kwargs = client.http_request.call_args.kwargs
    assert kwargs["data"]["userCode"] == 1234


def test_update_zones_auto_bypasses_new_low_battery_zone_when_enabled():
    """When auto_bypass_low_battery is enabled, a newly-seen low-battery zone that can
    be bypassed is bypassed automatically during a panel status refresh."""
    client = Mock()
    client.raise_for_resultcode.return_value = None
    client.http_request.return_value = {"ResultCode": 0, "ResultData": "Success"}
    location = TotalConnectLocation(RESULT_LOCATION, client)
    location.auto_bypass_low_battery = True

    zone_data = {
        "ZoneID": 42,
        "ZoneDescription": "Low battery sensor",
        "ZoneStatus": ZoneStatus.LOW_BATTERY,
        "CanBeBypassed": 1,
        "PartitionId": 1,
    }
    location._update_zones([zone_data])

    assert location.zones[42].is_low_battery() is True
    kwargs = client.http_request.call_args.kwargs
    assert kwargs["data"]["ZoneIds"] == [42]


def test_arm_custom_is_not_operational_yet():
    """arm_custom() is documented as not operational and must not silently succeed."""
    location = TotalConnectLocation(RESULT_LOCATION, Mock())
    with raises(TotalConnectError):
        location.arm_custom(ArmType.AWAY)


def test_get_custom_arm_settings_is_not_operational_yet():
    """get_custom_arm_settings() is documented as not operational and must not
    silently return fabricated data."""
    location = TotalConnectLocation(RESULT_LOCATION, Mock())
    with raises(TotalConnectError):
        location.get_custom_arm_settings()


def test_sync_panel_sends_usercode_and_stores_job_id():
    """sync_panel() sends the location's usercode and records the returned JobID."""
    client = Mock()
    client.raise_for_resultcode.return_value = None
    client.http_request.return_value = REST_RESULT_SECURITY_SYNCHRONIZE
    location = TotalConnectLocation(RESULT_LOCATION, client)
    location.usercode = "1234"

    location.sync_panel()

    kwargs = client.http_request.call_args.kwargs
    assert kwargs["data"]["userCode"] == "1234"
    assert location._sync_job_id == REST_RESULT_SECURITY_SYNCHRONIZE["JobID"]


def test_trigger_sends_remote_panic_alarm_request():
    """trigger() calls the RemotePanicAlarm endpoint for this location's security device."""
    client = Mock()
    client.raise_for_resultcode.return_value = None
    client.http_request.return_value = {"ResultCode": 0, "ResultData": "Success"}
    location = TotalConnectLocation(RESULT_LOCATION, client)

    location.trigger()

    kwargs = client.http_request.call_args.kwargs
    assert "RemotePanicAlarm" in kwargs["endpoint"]


def test_get_cameras_does_nothing_when_no_camera_list_present():
    """get_cameras() does not raise when the account has no cameras configured."""
    client = Mock()
    client.raise_for_resultcode.return_value = None
    client.http_request.return_value = {"ResultCode": 0, "ResultData": "Success"}
    location = TotalConnectLocation(RESULT_LOCATION, client)
    location.get_cameras()


def test_get_cameras_attaches_doorbell_and_video_info_to_matching_devices():
    """get_cameras() attaches WiFi doorbell and VideoPIR info to the devices they
    belong to, identified by DeviceID."""
    client = Mock()
    client.raise_for_resultcode.return_value = None
    location = TotalConnectLocation(RESULT_LOCATION, client)
    device_id = list(location.devices)[0]

    client.http_request.return_value = {
        "ResultCode": 0,
        "AccountAllCameraList": {
            "WiFiDoorbellList": {
                "WiFiDoorbellsList": {
                    "WiFiDoorBellInfo": [
                        {"DeviceID": device_id, "IsExistingDoorBellUser": 1},
                        {"DeviceID": "not-a-real-device", "IsExistingDoorBellUser": 1},
                    ]
                }
            },
            "VideoPirList": {"VideoPirInfo": [{"DeviceID": device_id, "SomeVideoKey": "x"}]},
        },
    }

    location.get_cameras()

    assert location.devices[device_id].doorbell_info == {
        "DeviceID": device_id,
        "IsExistingDoorBellUser": 1,
    }
    assert location.devices[device_id].video_info == {"DeviceID": device_id, "SomeVideoKey": "x"}
