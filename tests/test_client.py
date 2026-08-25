"""Test TotalConnectClient."""

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


def test_raise_for_resultcode_treats_an_absent_result_code_as_success():
    """A response carrying no ResultCode is success, not an error.

    Not every TotalConnect call returns a ResultCode. `_ResultCode.from_response`
    reads "ResultCode" then "error", and treats a falsy result as SUCCESS --
    the behaviour documented in docs/RESULT_CODES.md ("if there is no ResultCode
    and no error, then there was success") and the answer to issue #228
    ("Handle ResponseCode is None").

    Nothing pinned it. A refactor tightening this into an error would break
    every endpoint that legitimately omits the field, and the failure would
    appear as spurious exceptions on calls that had always worked.

    Note the deliberate consequence: an empty response is also SUCCESS. Callers
    are expected to raise PartialResponseError when data they need is missing,
    which is the layer that actually catches an unusable response.
    """
    client = create_http_client()

    for response in ({"ResultData": "Success"}, {"ResultCode": None}, {"ResultCode": 0}, {}):
        client.raise_for_resultcode(response)  # must not raise

    assert _ResultCode.from_response({}) is _ResultCode.SUCCESS
    assert _ResultCode.from_response({"ResultCode": None}) is _ResultCode.SUCCESS


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


def test_raise_for_resultcode_invalid_parameter_is_named_not_unknown():
    """INVALID_PARAMETER is in the enum but has no dedicated handler.

    -501 takes a different path from a genuinely unknown code: from_response()
    resolves it to a _ResultCode, then raise_for_resultcode() falls through every
    specific branch to the generic BadResultCodeError. Enum membership is what
    makes the message the code's name instead of "unknown result code -501", and
    that message is the only observable difference — so it is what this pins.
    Without it, deleting the enum member would look like a no-op.
    """
    client = create_http_client()
    with raises(BadResultCodeError) as excinfo:
        client.raise_for_resultcode({"ResultCode": _ResultCode.INVALID_PARAMETER.value})

    assert excinfo.value.args[0] == "INVALID_PARAMETER"


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
