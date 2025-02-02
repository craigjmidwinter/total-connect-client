"""Test client authentication."""

from unittest.mock import patch

import pytest
import requests_mock
from common import create_client
from const import HTTP_RESPONSE_BAD_USER_OR_PASSWORD

from total_connect_client.const import AUTH_TOKEN_ENDPOINT,HTTP_API_LOGOUT, _ResultCode
from total_connect_client.exceptions import AuthenticationError, TotalConnectError
from total_connect_client.client import TotalConnectClient

RESPONSE_SUCCESS = {
    "ResultCode": _ResultCode.SUCCESS.value,
    "ResultData": "None",
    "SessionID": "123456890",
}


def mock_log_out(client: TotalConnectClient, response)->None:
    """Logout client with given response."""
    with requests_mock.Mocker(real_http=True) as rm:
        rm.post(HTTP_API_LOGOUT,json=response)
        client.log_out()


def tests_logout():
    """Test logout."""
    client = create_client()
    assert client.is_logged_in() is True

    RESPONSE_LOGOUT_FAILURE = {
        "ResultCode": 1,
        "ResultData": "some error"
    }

    with pytest.raises(TotalConnectError):
        mock_log_out(client, RESPONSE_LOGOUT_FAILURE)
    assert client.is_logged_in() is True

    mock_log_out(client, RESPONSE_SUCCESS)
    assert client.is_logged_in() is False

    # succeeds without API call because we are logged out
    assert client.is_logged_in() is False


def tests_authenticate():
    """Test authenticate()."""
    client = create_client()

    # ensure logged out to start
    mock_log_out(client, RESPONSE_SUCCESS)
    assert client.is_logged_in() is False

    client.authenticate()
    assert client.is_logged_in() is True

    mock_log_out(client, RESPONSE_SUCCESS)
    assert client.is_logged_in() is False

    # bad user or pass
    with requests_mock.Mocker(real_http=True) as rm, pytest.raises(
        AuthenticationError
    ):
        rm.post(
            AUTH_TOKEN_ENDPOINT,
            json=HTTP_RESPONSE_BAD_USER_OR_PASSWORD,
            status_code=403,
        )
        client.authenticate()
    assert client.is_logged_in() is False

    RESPONSE = {
        "ResultCode": _ResultCode.AUTHENTICATION_FAILED,
        "ResultData": "some error"
    }

    # authentication failed
    with requests_mock.Mocker(real_http=True) as rm, pytest.raises(
        AuthenticationError
    ):
        rm.post(
            AUTH_TOKEN_ENDPOINT,
            json=RESPONSE,
        )
        client.authenticate()
    assert client.is_logged_in() is False

    # authentication locked
    RESPONSE["ResultCode"] = _ResultCode.ACCOUNT_LOCKED
    with requests_mock.Mocker(real_http=True) as rm, pytest.raises(
        AuthenticationError
    ):
        rm.post(
            AUTH_TOKEN_ENDPOINT,
            json=RESPONSE,
        )
        client.authenticate()
    assert client.is_logged_in() is False
