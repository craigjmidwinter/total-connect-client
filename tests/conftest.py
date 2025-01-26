import pytest
import requests_mock

from total_connect_client.client import TotalConnectClient

from const import (
    HTTP_RESPONSE_CONFIG,
    HTTP_RESPONSE_TOKEN,
    HTTP_RESPONSE_TOKEN_2
)

@pytest.fixture(autouse=True)
def mock_http_requests():
    """Automatically mock any direct HTTP requests, right now these are used for authentication only."""
    with requests_mock.Mocker() as rm:
        rm.get(TotalConnectClient.CONFIG_ENDPOINT, json=HTTP_RESPONSE_CONFIG, status_code=200)
        rm.post(TotalConnectClient.TOKEN_ENDPOINT, json=HTTP_RESPONSE_TOKEN, status_code=200)
        yield
