"""Test client authentication."""

from unittest.mock import patch

import pytest
import requests_mock
from common import create_client
from const import HTTP_RESPONSE_BAD_USER_OR_PASSWORD

from total_connect_client.const import AUTH_TOKEN_ENDPOINT, _ResultCode
from total_connect_client.exceptions import AuthenticationError

RESPONSE_SUCCESS = {
    "ResultCode": _ResultCode.SUCCESS.value,
    "ResultData": "None",
    "SessionID": "123456890",
}


def tests_logout():
    """Test logout."""
    client = create_client()
    responses = [
        RESPONSE_SUCCESS,
    ]
    with patch(
        "total_connect_client.client.TotalConnectClient.request",
        side_effect=responses,
    ):
        assert client.is_logged_in() is True
        client.log_out()
        assert client.is_logged_in() is False

        # succeeds because we are logged out
        client.log_out()


def tests_authenticate():
    """Test authenticate()."""
    client = create_client()
    responses = [
        RESPONSE_SUCCESS,
        RESPONSE_SUCCESS,
    ]
    with patch(
        "total_connect_client.client.TotalConnectClient.request",
        side_effect=responses,
    ), patch(
        "total_connect_client.client.TotalConnectClient._make_locations",
        return_value=["fakelocations"],
    ):
        # ensure we start logged out (first SUCCESS)
        client.log_out()
        assert client.is_logged_in() is False

        # success (second SUCCESS)
        client.authenticate()
        assert client.is_logged_in() is True

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

        # authentication failed
        with pytest.raises(AuthenticationError):
            client.authenticate()
        assert client.is_logged_in() is False
