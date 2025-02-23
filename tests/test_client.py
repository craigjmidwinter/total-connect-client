"""Test TotalConnectClient."""

import requests_mock
from pytest import raises
from common import create_http_client
from const import REST_RESULT_LOGOUT, RESPONSE_UNKNOWN
from total_connect_client.const import HTTP_API_LOGOUT
from total_connect_client.exceptions import TotalConnectError


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
