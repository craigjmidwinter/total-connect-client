"""Test TotalConnectClient."""

from unittest.mock import Mock

import requests
import requests_mock
from common import create_http_client
from const import (
    HTTP_RESPONSE_BAD_USER_OR_PASSWORD,
    HTTP_RESPONSE_CONFIG,
    HTTP_RESPONSE_SESSION_DETAILS_EMPTY,
    HTTP_RESPONSE_TOKEN,
    LOCATION_ID,
    PANEL_STATUS_ARMED_AWAY,
    PANEL_STATUS_DISARMED,
    RESPONSE_CONNECTION_ERROR,
    RESPONSE_INVALID_SESSION,
    RESPONSE_UNKNOWN,
    REST_RESULT_LOGOUT,
    REST_RESULT_PARTITIONS_CONFIG,
    REST_RESULT_PARTITIONS_ZONES,
    REST_RESULT_SESSION_DETAILS,
    SECURITY_DEVICE_ID,
)
from pytest import raises

from total_connect_client.client import TotalConnectClient
from total_connect_client.const import (
    AUTH_CONFIG_ENDPOINT,
    AUTH_TOKEN_ENDPOINT,
    HTTP_API_LOGOUT,
    HTTP_API_SESSION_DETAILS_ENDPOINT,
    _ResultCode,
    make_http_endpoint,
)
from total_connect_client.exceptions import (
    AuthenticationError,
    BadResultCodeError,
    FailedToBypassZone,
    FeatureNotSupportedError,
    InvalidSessionError,
    PartialResponseError,
    RetryableTotalConnectError,
    ServiceUnavailable,
    TotalConnectError,
    UsercodeInvalid,
    UsercodeUnavailable,
)


def tests_logout():
    """Test log_out."""
    client = create_http_client()
    assert client.is_logged_in() is True

    with requests_mock.Mocker() as rm:
        # first give an error
        rm.post(HTTP_API_LOGOUT, json=RESPONSE_UNKNOWN)
        with raises(TotalConnectError):
            client.log_out()
        assert client.is_logged_in() is True

        # then give success
        rm.post(HTTP_API_LOGOUT, json=REST_RESULT_LOGOUT)
        client.log_out()
        assert client.is_logged_in() is False


def test_get_configuration_connection_reset_all_fail():
    """Test that ServiceUnavailable is raised when ConnectionResetError persists across all retries.

    Regression test for https://github.com/home-assistant/core/issues/174207
    """
    with requests_mock.Mocker() as rm:
        rm.get(
            AUTH_CONFIG_ENDPOINT,
            exc=requests.exceptions.ConnectionError("Connection reset by peer"),
        )
        with raises(ServiceUnavailable):
            TotalConnectClient("username", "password", {}, retry_delay=0)


def test_get_configuration_connection_reset_then_success():
    """Test that a transient ConnectionResetError on _get_configuration is retried and recovers.

    Regression test for https://github.com/home-assistant/core/issues/174207
    """
    with requests_mock.Mocker() as rm:
        rm.get(
            AUTH_CONFIG_ENDPOINT,
            response_list=[
                {"exc": requests.exceptions.ConnectionError("Connection reset by peer")},
                {"json": HTTP_RESPONSE_CONFIG},
            ],
        )
        rm.post(AUTH_TOKEN_ENDPOINT, json=HTTP_RESPONSE_TOKEN)
        rm.get(HTTP_API_SESSION_DETAILS_ENDPOINT, json=REST_RESULT_SESSION_DETAILS)
        rm.get(
            make_http_endpoint(
                f"api/v1/locations/{LOCATION_ID}/devices/{SECURITY_DEVICE_ID}/partitions/config"
            ),
            json=REST_RESULT_PARTITIONS_CONFIG,
        )
        rm.get(
            make_http_endpoint(f"api/v1/locations/{LOCATION_ID}/partitions/zones/0"),
            json=REST_RESULT_PARTITIONS_ZONES,
        )
        rm.get(
            make_http_endpoint(f"api/v3/locations/{LOCATION_ID}/partitions/fullStatus"),
            json=PANEL_STATUS_DISARMED,
        )

        client = TotalConnectClient("username", "password", {LOCATION_ID: "1234"}, retry_delay=0)
        assert client.is_logged_in() is True


def test_http_request_retries_on_retryable_result_code_then_succeeds():
    """A CONNECTION_ERROR ResultCode is treated as transient: the request is retried
    automatically and the caller never sees an exception if a later attempt succeeds."""
    with requests_mock.Mocker() as rm:
        rm.get(AUTH_CONFIG_ENDPOINT, json=HTTP_RESPONSE_CONFIG)
        rm.post(AUTH_TOKEN_ENDPOINT, json=HTTP_RESPONSE_TOKEN)
        rm.get(HTTP_API_SESSION_DETAILS_ENDPOINT, json=REST_RESULT_SESSION_DETAILS)
        rm.get(
            make_http_endpoint(
                f"api/v1/locations/{LOCATION_ID}/devices/{SECURITY_DEVICE_ID}/partitions/config"
            ),
            json=REST_RESULT_PARTITIONS_CONFIG,
        )
        rm.get(
            make_http_endpoint(f"api/v1/locations/{LOCATION_ID}/partitions/zones/0"),
            json=REST_RESULT_PARTITIONS_ZONES,
        )
        rm.get(
            make_http_endpoint(f"api/v3/locations/{LOCATION_ID}/partitions/fullStatus"),
            response_list=[
                {"json": RESPONSE_CONNECTION_ERROR},
                {"json": PANEL_STATUS_DISARMED},
            ],
        )

        client = TotalConnectClient("username", "password", {LOCATION_ID: "1234"}, retry_delay=0)
        location = client.locations[LOCATION_ID]
        assert location.arming_state.is_disarmed()


def test_get_panel_meta_data_reauthenticates_after_invalid_session_then_succeeds():
    """An invalid/expired session ResultCode triggers a fresh login and a retry of the
    original request, rather than surfacing the session error to the caller."""
    client = create_http_client(PANEL_STATUS_DISARMED)
    location = client.locations[LOCATION_ID]

    with requests_mock.Mocker() as rm:
        rm.get(AUTH_CONFIG_ENDPOINT, json=HTTP_RESPONSE_CONFIG)
        rm.post(AUTH_TOKEN_ENDPOINT, json=HTTP_RESPONSE_TOKEN)
        rm.get(
            make_http_endpoint(f"api/v3/locations/{LOCATION_ID}/partitions/fullStatus"),
            response_list=[
                {"json": RESPONSE_INVALID_SESSION},
                {"json": PANEL_STATUS_ARMED_AWAY},
            ],
        )

        location.get_panel_meta_data()
        assert location.arming_state.is_armed_away()


def test_raise_for_resultcode_success_does_not_raise():
    """ResultCode SUCCESS (0) is not an error."""
    client = create_http_client()
    client.raise_for_resultcode({"ResultCode": _ResultCode.SUCCESS.value})


def test_raise_for_resultcode_arm_success_does_not_raise():
    """ResultCode 4500 (shared by ARM_SUCCESS/DISARM_SUCCESS/SESSION_INITIATED) is not an error."""
    client = create_http_client()
    client.raise_for_resultcode({"ResultCode": _ResultCode.ARM_SUCCESS.value})


def test_raise_for_resultcode_bad_user_or_password_raises_authentication_error():
    """BAD_USER_OR_PASSWORD maps to AuthenticationError."""
    client = create_http_client()
    with raises(AuthenticationError):
        client.raise_for_resultcode({"ResultCode": _ResultCode.BAD_USER_OR_PASSWORD.value})


def test_raise_for_resultcode_authentication_failed_raises_authentication_error():
    """AUTHENTICATION_FAILED maps to AuthenticationError."""
    client = create_http_client()
    with raises(AuthenticationError):
        client.raise_for_resultcode({"ResultCode": _ResultCode.AUTHENTICATION_FAILED.value})


def test_raise_for_resultcode_account_locked_raises_authentication_error():
    """ACCOUNT_LOCKED maps to AuthenticationError."""
    client = create_http_client()
    with raises(AuthenticationError):
        client.raise_for_resultcode({"ResultCode": _ResultCode.ACCOUNT_LOCKED.value})


def test_raise_for_resultcode_user_code_unavailable_raises_usercode_unavailable():
    """USER_CODE_UNAVAILABLE maps to UsercodeUnavailable."""
    client = create_http_client()
    with raises(UsercodeUnavailable):
        client.raise_for_resultcode({"ResultCode": _ResultCode.USER_CODE_UNAVAILABLE.value})


def test_raise_for_resultcode_user_code_invalid_raises_usercode_invalid():
    """USER_CODE_INVALID maps to UsercodeInvalid."""
    client = create_http_client()
    with raises(UsercodeInvalid):
        client.raise_for_resultcode({"ResultCode": _ResultCode.USER_CODE_INVALID.value})


def test_raise_for_resultcode_feature_not_supported_raises_feature_not_supported_error():
    """FEATURE_NOT_SUPPORTED maps to FeatureNotSupportedError."""
    client = create_http_client()
    with raises(FeatureNotSupportedError):
        client.raise_for_resultcode({"ResultCode": _ResultCode.FEATURE_NOT_SUPPORTED.value})


def test_raise_for_resultcode_failed_to_bypass_zone_raises_failed_to_bypass_zone():
    """FAILED_TO_BYPASS_ZONE maps to FailedToBypassZone."""
    client = create_http_client()
    with raises(FailedToBypassZone):
        client.raise_for_resultcode({"ResultCode": _ResultCode.FAILED_TO_BYPASS_ZONE.value})


def test_raise_for_resultcode_unknown_code_raises_bad_result_code_error():
    """Any ResultCode not otherwise mapped raises the generic BadResultCodeError."""
    client = create_http_client()
    with raises(BadResultCodeError):
        client.raise_for_resultcode(RESPONSE_UNKNOWN)


def test_raise_for_resultcode_invalid_session_raises_invalid_session_error():
    """INVALID_SESSION maps to InvalidSessionError."""
    client = create_http_client()
    with raises(InvalidSessionError):
        client.raise_for_resultcode({"ResultCode": _ResultCode.INVALID_SESSION.value})


def test_raise_for_resultcode_invalid_sessionid_raises_invalid_session_error():
    """INVALID_SESSIONID maps to InvalidSessionError."""
    client = create_http_client()
    with raises(InvalidSessionError):
        client.raise_for_resultcode({"ResultCode": _ResultCode.INVALID_SESSIONID.value})


def test_raise_for_resultcode_connection_error_raises_retryable_error():
    """CONNECTION_ERROR maps to RetryableTotalConnectError."""
    client = create_http_client()
    with raises(RetryableTotalConnectError):
        client.raise_for_resultcode({"ResultCode": _ResultCode.CONNECTION_ERROR.value})


def test_raise_for_resultcode_failed_to_connect_raises_retryable_error():
    """FAILED_TO_CONNECT maps to RetryableTotalConnectError."""
    client = create_http_client()
    with raises(RetryableTotalConnectError):
        client.raise_for_resultcode({"ResultCode": _ResultCode.FAILED_TO_CONNECT.value})


def test_raise_for_resultcode_cannot_connect_raises_retryable_error():
    """CANNOT_CONNECT maps to RetryableTotalConnectError."""
    client = create_http_client()
    with raises(RetryableTotalConnectError):
        client.raise_for_resultcode({"ResultCode": _ResultCode.CANNOT_CONNECT.value})


def test_raise_for_resultcode_bad_object_reference_raises_retryable_error():
    """BAD_OBJECT_REFERENCE maps to RetryableTotalConnectError."""
    client = create_http_client()
    with raises(RetryableTotalConnectError):
        client.raise_for_resultcode({"ResultCode": _ResultCode.BAD_OBJECT_REFERENCE.value})


def test_get_number_locations_returns_count_of_locations():
    """get_number_locations() reflects the number of locations on the account."""
    client = create_http_client()
    assert client.get_number_locations() == len(client.locations)
    assert client.get_number_locations() == 1


def test_times_as_string_reports_init_and_total_running_time():
    """times_as_string() includes both setup and total timing, for diagnostics."""
    client = create_http_client()
    report = client.times_as_string()
    assert "__init__" in report
    assert "total running time" in report


def test_log_out_does_nothing_when_already_logged_out():
    """log_out() is a no-op (no HTTP call) if the client is not logged in."""
    client = create_http_client()
    client._logged_in = False
    with requests_mock.Mocker() as rm:
        client.log_out()
        assert rm.call_count == 0


def test_make_locations_uses_default_usercode_when_none_provided():
    """A location with no matching entry in the usercodes dict falls back to the
    client's default usercode rather than being left unusable."""
    with requests_mock.Mocker() as rm:
        rm.get(AUTH_CONFIG_ENDPOINT, json=HTTP_RESPONSE_CONFIG)
        rm.post(AUTH_TOKEN_ENDPOINT, json=HTTP_RESPONSE_TOKEN)
        rm.get(HTTP_API_SESSION_DETAILS_ENDPOINT, json=REST_RESULT_SESSION_DETAILS)
        rm.get(
            make_http_endpoint(
                f"api/v1/locations/{LOCATION_ID}/devices/{SECURITY_DEVICE_ID}/partitions/config"
            ),
            json=REST_RESULT_PARTITIONS_CONFIG,
        )
        rm.get(
            make_http_endpoint(f"api/v1/locations/{LOCATION_ID}/partitions/zones/0"),
            json=REST_RESULT_PARTITIONS_ZONES,
        )
        rm.get(
            make_http_endpoint(f"api/v3/locations/{LOCATION_ID}/partitions/fullStatus"),
            json=PANEL_STATUS_DISARMED,
        )

        # no usercodes at all for this location
        client = TotalConnectClient("username", "password", {})
        location = client.locations[LOCATION_ID]
        assert location.usercode == "-1"


def test_authenticate_with_bad_credentials_raises_authentication_error():
    """A rejected username/password raises AuthenticationError."""
    with requests_mock.Mocker() as rm:
        rm.get(AUTH_CONFIG_ENDPOINT, json=HTTP_RESPONSE_CONFIG)
        rm.post(AUTH_TOKEN_ENDPOINT, json=HTTP_RESPONSE_BAD_USER_OR_PASSWORD, status_code=400)

        with raises(AuthenticationError):
            TotalConnectClient("baduser", "badpass", {})


def test_authenticate_raises_immediately_once_credentials_are_known_bad():
    """Once a client has recorded that its credentials are invalid, re-authenticating
    fails fast with AuthenticationError instead of hitting the network again."""
    client = create_http_client()
    client._invalid_credentials = True
    with requests_mock.Mocker() as rm:
        with raises(AuthenticationError):
            client.authenticate()
        assert rm.call_count == 0


def test_get_session_details_raises_when_account_has_no_locations():
    """An account with no locations is treated as an error, not an empty client."""
    with requests_mock.Mocker() as rm:
        rm.get(AUTH_CONFIG_ENDPOINT, json=HTTP_RESPONSE_CONFIG)
        rm.post(AUTH_TOKEN_ENDPOINT, json=HTTP_RESPONSE_TOKEN)
        rm.get(HTTP_API_SESSION_DETAILS_ENDPOINT, json=HTTP_RESPONSE_SESSION_DETAILS_EMPTY)

        with raises(TotalConnectError):
            TotalConnectClient("username", "password", {})


def test_log_out_raises_total_connect_error_when_resultcode_nonzero_after_success_alias():
    """log_out() raises if the logout response's literal ResultCode is not 0, even
    though 4500 (an alias shared with ARM/DISARM/SESSION_INITIATED success codes) is
    not itself treated as an authentication/retry error."""
    client = create_http_client()
    with requests_mock.Mocker() as rm:
        rm.post(
            HTTP_API_LOGOUT,
            json={"ResultCode": _ResultCode.SESSION_INITIATED.value, "ResultData": "weird"},
        )
        with raises(TotalConnectError):
            client.log_out()


def test_load_details_keeps_a_reachable_location_when_another_fails():
    """One unreachable panel must not cost the user their other locations.

    Regression test for issue #263 ("client.locations raises if any panel cannot
    be contacted"). Before that fix, a user whose account held several locations
    could be left unable to use the client at all when a single panel was
    unreachable. load_details() now records success per location, retries only
    the ones still outstanding, and warns rather than raising once retries are
    exhausted.

    No fixture defines a second location, so the two locations are mocked
    directly -- the behaviour under test is load_details()' own bookkeeping, not
    the HTTP layer.
    """
    client = create_http_client()
    good_id, bad_id = LOCATION_ID, 7654321
    good, bad = Mock(), Mock()
    bad.get_partition_details.side_effect = PartialResponseError("no PartitionDetails", {})

    client._locations = {good_id: good, bad_id: bad}
    client._location_details = {good_id: False, bad_id: False}

    client.load_details(retries=1)

    # the reachable location is fully loaded despite its neighbour failing
    assert client._location_details[good_id] is True
    assert client._location_details[bad_id] is False

    # and it is fetched once, not re-fetched on the retry pass
    assert good.get_partition_details.call_count == 1
    assert good.get_zone_details.call_count == 1

    # the failing location is retried, then given up on without raising
    assert bad.get_partition_details.call_count == 2


def test_make_locations_resolves_a_usercode_per_location():
    """Each location gets its own usercode, by int key, str key, or "default".

    The usercodes dict is keyed per location because a code belongs to a
    (user, location) pair rather than to the user -- the lesson of issue #85,
    fixed in PR #88. The lookup tries the int key, then the str key, then
    "default", and falls back to the DEFAULT_USERCODE sentinel when none match.

    Every fixture defines a single location, so that chain has only ever been
    exercised with one entry. This walks all four outcomes at once.
    """
    client = create_http_client()
    base = REST_RESULT_SESSION_DETAILS["SessionDetailsResult"]["Locations"][0]

    def location(location_id):
        return {**base, "LocationID": location_id, "LocationName": f"loc{location_id}"}

    client.usercodes = {111111: "1111", "222222": "2222", "default": "9999"}
    client._locations = {}
    client._location_details = {}
    client._make_locations(
        {"Locations": [location(111111), location(222222), location(333333), location(444444)]}
    )

    assert client.locations[111111].usercode == "1111"  # matched on the int key
    assert client.locations[222222].usercode == "2222"  # matched on the str key
    assert client.locations[333333].usercode == "9999"  # fell back to "default"

    # a fourth location with no match and no default would get the sentinel;
    # here "default" is present, so every location resolves to a real code
    assert client.locations[444444].usercode == "9999"
