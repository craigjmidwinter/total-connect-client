"""Common test code."""
from unittest.mock import patch
import requests_mock

from const import (
    LOCATION_INFO_BASIC_NORMAL,
    RESPONSE_DISARMED, RESPONSE_GET_ZONE_DETAILS_SUCCESS, RESPONSE_PARTITION_DETAILS,
    HTTP_RESPONSE_PARTITION_DETAILS,
    HTTP_RESPONSE_STATUS_DISARMED,
    HTTP_RESPONSE_ZONE_DETAILS,
    HTTP_RESPONSE_SESSION_DETAILS, HTTP_RESPONSE_CONFIG, HTTP_RESPONSE_TOKEN

)

from total_connect_client.client import TotalConnectClient
from total_connect_client.const import (
    AUTH_CONFIG_ENDPOINT,
    AUTH_TOKEN_ENDPOINT,
    HTTP_API_SESSION_DETAILS_ENDPOINT, make_http_endpoint
)

def create_client():
    """Return a TotalConnectClient that appears to be logged in."""
    responses = [
        RESPONSE_PARTITION_DETAILS,
        RESPONSE_GET_ZONE_DETAILS_SUCCESS,
        RESPONSE_DISARMED,
    ]

    with patch(
        "total_connect_client.client.TotalConnectClient.request", side_effect=responses
    ):
        mock_client = TotalConnectClient("username", "password", {"123456": "1234"})
        if mock_client.locations:  # force client to fetch them
            pass

    return mock_client

def create_http_client():
    """Return a TotalConnectClient that appears to be logged in."""
    location_id = LOCATION_INFO_BASIC_NORMAL["LocationID"]
    security_device_id = LOCATION_INFO_BASIC_NORMAL["SecurityDeviceID"]

    with requests_mock.Mocker() as rm:
        rm.get(AUTH_CONFIG_ENDPOINT, json=HTTP_RESPONSE_CONFIG)
        rm.post(AUTH_TOKEN_ENDPOINT, json=HTTP_RESPONSE_TOKEN)
        rm.get(
            HTTP_API_SESSION_DETAILS_ENDPOINT,
            json=HTTP_RESPONSE_SESSION_DETAILS,
        )
        rm.get(make_http_endpoint(f"api/v1/locations/{location_id}/devices/{security_device_id}/partitions/config"), json=HTTP_RESPONSE_PARTITION_DETAILS)
        rm.get(make_http_endpoint(f"api/v1/locations/{location_id}/partitions/zones/0"), json=HTTP_RESPONSE_ZONE_DETAILS)
        rm.get(make_http_endpoint(f"api/v3/locations/{location_id}/partitions/fullStatus"), json=HTTP_RESPONSE_STATUS_DISARMED)

        mock_client = TotalConnectClient("username", "password", {"123456": "1234"})
        if mock_client.locations:  # force client to fetch them
            pass

    return mock_client
