"""Global test fixtures."""

import pytest
import requests_mock
from const import (
    HTTP_RESPONSE_CONFIG,
    HTTP_RESPONSE_SESSION_DETAILS,
    HTTP_RESPONSE_TOKEN,
)

from total_connect_client.const import (
    AUTH_CONFIG_ENDPOINT,
    AUTH_TOKEN_ENDPOINT,
    HTTP_API_SESSION_DETAILS_ENDPOINT,
)


@pytest.fixture(autouse=True)
def mock_http_requests():
    """Automatically mock any direct HTTP requests, right now these are used for authentication only."""
    with requests_mock.Mocker() as rm:
        rm.get(AUTH_CONFIG_ENDPOINT, json=HTTP_RESPONSE_CONFIG, status_code=200)
        rm.post(AUTH_TOKEN_ENDPOINT, json=HTTP_RESPONSE_TOKEN, status_code=200)
        rm.get(
            HTTP_API_SESSION_DETAILS_ENDPOINT,
            json=HTTP_RESPONSE_SESSION_DETAILS,
            status_code=200,
        )
        yield
