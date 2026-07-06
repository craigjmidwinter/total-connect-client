"""Test TotalConnectClient."""

import requests
import requests_mock
from common import create_http_client
from const import (
    HTTP_RESPONSE_CONFIG,
    HTTP_RESPONSE_TOKEN,
    LOCATION_ID,
    PANEL_STATUS_DISARMED,
    REST_RESULT_LOGOUT,
    REST_RESULT_PARTITIONS_CONFIG,
    REST_RESULT_PARTITIONS_ZONES,
    REST_RESULT_SESSION_DETAILS,
    RESPONSE_UNKNOWN,
    SECURITY_DEVICE_ID,
)
from pytest import raises

from total_connect_client.client import TotalConnectClient
from total_connect_client.const import (
    AUTH_CONFIG_ENDPOINT,
    AUTH_TOKEN_ENDPOINT,
    HTTP_API_LOGOUT,
    HTTP_API_SESSION_DETAILS_ENDPOINT,
    make_http_endpoint,
)
from total_connect_client.exceptions import ServiceUnavailable, TotalConnectError


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

        client = TotalConnectClient(
            "username", "password", {LOCATION_ID: "1234"}, retry_delay=0
        )
        assert client.is_logged_in() is True
