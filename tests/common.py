"""Common test code."""
from unittest.mock import patch

from const import (
    RESPONSE_AUTHENTICATE,
    RESPONSE_DISARMED,
    RESPONSE_GET_ZONE_DETAILS_SUCCESS,
    RESPONSE_PARTITION_DETAILS,
)

from total_connect_client.client import TotalConnectClient


def create_client():
    """Return a TotalConnectClient that appears to be logged in."""
    responses = [
        RESPONSE_AUTHENTICATE,
        RESPONSE_PARTITION_DETAILS,
        RESPONSE_GET_ZONE_DETAILS_SUCCESS,
        RESPONSE_DISARMED,
    ]

    with patch(
        "total_connect_client.client.TotalConnectClient.request", side_effect=responses
    ) as mock_request:
        mock_client = TotalConnectClient("username", "password", {"123456": "1234"})
        assert mock_request.call_count == 1
        if mock_client.locations:  # force client to fetch them
            pass
        assert mock_request.call_count == 4

    return mock_client
