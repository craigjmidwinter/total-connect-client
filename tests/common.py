"""Common test code."""
from unittest.mock import patch

import TotalConnectClient
from const import (
    RESPONSE_AUTHENTICATE,
    RESPONSE_DISARMED,
    RESPONSE_GET_ZONE_DETAILS_SUCCESS,
)


def create_client():
    """Return a TotalConnectClient that appears to be logged in."""
    RESPONSES = [
        RESPONSE_AUTHENTICATE,
        RESPONSE_GET_ZONE_DETAILS_SUCCESS,
        RESPONSE_DISARMED,
    ]

    with patch("zeep.Client", autospec=True), patch(
        "TotalConnectClient.TotalConnectClient.request", side_effect=RESPONSES,
    ) as mock_request:
        client = TotalConnectClient.TotalConnectClient("username", "password")
        assert mock_request.call_count == 3

    return client
