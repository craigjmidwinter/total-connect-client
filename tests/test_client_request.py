"""Test total_connect_client request()."""

import unittest
from unittest.mock import patch
from zeep.exceptions import Fault as ZeepFault

import pytest
import requests_mock
from const import (
    MAX_RETRY_ATTEMPTS,
    LOCATION_INFO_BASIC_NORMAL,
    RESPONSE_ARMED_AWAY,
    RESPONSE_SESSION_DETAILS,
    RESPONSE_CONNECTION_ERROR,
    RESPONSE_DISARMED,
    RESPONSE_FAILED_TO_CONNECT,
    RESPONSE_GET_ZONE_DETAILS_SUCCESS,
    RESPONSE_INVALID_SESSION,
    RESPONSE_PARTITION_DETAILS,
    RESPONSE_UNKNOWN,
    HTTP_RESPONSE_TOKEN,
    HTTP_RESPONSE_TOKEN_2,
    HTTP_RESPONSE_BAD_USER_OR_PASSWORD,
    HTTP_RESPONSE_REFRESH_TOKEN_FAILED,
    SESSION_ID,
    SESSION_ID_2,
    TOKEN_EXPIRATION_TIME
)

from total_connect_client.const import ArmType
from total_connect_client.client import TotalConnectClient
from total_connect_client.exceptions import AuthenticationError, BadResultCodeError, ServiceUnavailable

PATCH_EVAL = "total_connect_client.client.TotalConnectClient._send_one_request"


class TestTotalConnectClient(unittest.TestCase):
    """Test TotalConnectClient request()."""

    def setUp(self):
        """Test setup."""
        self.client = None
        self.location_id = LOCATION_INFO_BASIC_NORMAL["LocationID"]

    def tearDown(self):
        """Test cleanup."""
        self.client = None

    def tests_request_init(self):
        """Test normal init sequence with no problems."""
        serialize_responses = [
            RESPONSE_SESSION_DETAILS,
            RESPONSE_PARTITION_DETAILS,
            RESPONSE_GET_ZONE_DETAILS_SUCCESS,
            RESPONSE_DISARMED,
        ]

        with patch("zeep.Client"), patch(
            PATCH_EVAL, side_effect=serialize_responses
        ) as mock_request:
            client = TotalConnectClient("username", "password", usercodes=None)
            assert mock_request.call_count == 1
            if client.locations:  # force client to fetch them
                pass
            assert mock_request.call_count == 4
            assert client.is_logged_in() is True

    def tests_request_init_bad_user_or_password(self):
        """Test init sequence with no a bad password."""
        with requests_mock.Mocker(real_http=True) as rm:
            rm.post(
                TotalConnectClient.TOKEN_ENDPOINT,
                json=HTTP_RESPONSE_BAD_USER_OR_PASSWORD,
                status_code=403
            )
            with pytest.raises(AuthenticationError):
                TotalConnectClient("username", "password", usercodes=None)

    def tests_request_init_failed_to_connect(self):
        """Test init sequence when it fails to connect."""
        serialize_responses = [
            RESPONSE_FAILED_TO_CONNECT for x in range(MAX_RETRY_ATTEMPTS)
        ]

        with patch("zeep.Client"), patch("time.sleep", autospec=True), patch(
            PATCH_EVAL, side_effect=serialize_responses
        ) as mock_request, pytest.raises(Exception) as exc:
            client = TotalConnectClient(
                "username", "password", usercodes=None, retry_delay=0
            )
            assert mock_request.call_count == MAX_RETRY_ATTEMPTS
            assert client.is_logged_in() is False
            expected = "total-connect-client could not execute request.  Maximum attempts tried."
            assert str(exc.value) == expected

    def tests_request_connection_error(self):
        """Test a connection error."""
        serialize_responses = [
            RESPONSE_CONNECTION_ERROR for x in range(MAX_RETRY_ATTEMPTS)
        ]

        with patch("zeep.Client"), patch("time.sleep", autospec=True), patch(
            "zeep.helpers.serialize_object", side_effect=serialize_responses
        ) as mock_request, pytest.raises(Exception) as exc:
            client = TotalConnectClient(
                "username", "password", usercodes=None, retry_delay=0
            )
            assert mock_request.call_count == MAX_RETRY_ATTEMPTS
            assert client.is_logged_in() is False
            expected = "total-connect-client could not execute request.  Maximum attempts tried."
            assert str(exc.value) == expected

    def tests_request_zeep_error(self):
        """Test a Zeep error."""

        serialize_responses = [ZeepFault("test") for x in range(MAX_RETRY_ATTEMPTS)]
        with patch("zeep.Client"), patch("time.sleep", autospec=True), patch(
            "zeep.helpers.serialize_object", side_effect=serialize_responses
        ) as mock_request, pytest.raises(ServiceUnavailable):
            client = TotalConnectClient(
                "username", "password", usercodes=None, retry_delay=0
            )
            assert mock_request.call_count == MAX_RETRY_ATTEMPTS
            assert client.is_logged_in() is False

    def tests_request_invalid_session(self):
        """Test an invalid session, which is when the session times out."""
        # First four responses set up 'normal' session
        # Call to client.arm_away() will first get an invalid session,
        # which will trigger client.authenticate() before completing the arm_away()
        serialize_responses = [
            RESPONSE_SESSION_DETAILS,
            RESPONSE_PARTITION_DETAILS,
            RESPONSE_GET_ZONE_DETAILS_SUCCESS,
            RESPONSE_DISARMED,
            RESPONSE_INVALID_SESSION,
            RESPONSE_ARMED_AWAY,
        ]

        token_responses = [
            {"json": HTTP_RESPONSE_TOKEN, "status_code": 200},
            {"json": HTTP_RESPONSE_TOKEN_2, "status_code": 200},
        ]

        with patch("zeep.Client"), patch(
            PATCH_EVAL, side_effect=serialize_responses
        ) as mock_request, requests_mock.Mocker(real_http=True) as rm:
            rm.post(TotalConnectClient.TOKEN_ENDPOINT, token_responses)
            client = TotalConnectClient("username", "password", usercodes=None)
            assert mock_request.call_count == 1
            if client.locations:  # force client to fetch them
                pass
            assert mock_request.call_count == 4
            assert client.is_logged_in() is True

            assert client.token == SESSION_ID
            # now try to arm away
            # the invalid session will trigger a new authenticate()...
            # which should result in a new token
            client.locations[LOCATION_INFO_BASIC_NORMAL["LocationID"]].arm(ArmType.AWAY)
            assert mock_request.call_count == 6
            assert client.token == SESSION_ID_2

    def tests_request_unknown_result_code(self):
        """Test an unknown result code."""
        serialize_responses = [
            RESPONSE_UNKNOWN,
        ]

        with patch("zeep.Client"), patch(
            PATCH_EVAL, side_effect=serialize_responses
        ) as mock_request:
            with pytest.raises(BadResultCodeError):
                TotalConnectClient("username", "password", usercodes=None)
            assert mock_request.call_count == 1

    def tests_empty_response_code(self):
        """Test an empty response code."""
        # see issue #228
        from total_connect_client.const import _ResultCode
        with pytest.raises(ServiceUnavailable):
            _ResultCode.from_response(None)

    def tests_refresh_session(self):
        """Test various scenarious around session refreshing. First the session expires and is
        successfully refreshed, then the session expires and the refresh fails, forcing a full
        reauthentication"""
        # First four responses set up 'normal' session
        # Call to client.arm_away() will first require a session refresh
        # Call to client.disarm() will first require a session refresh
        serialize_responses = [
            RESPONSE_SESSION_DETAILS,
            RESPONSE_PARTITION_DETAILS,
            RESPONSE_GET_ZONE_DETAILS_SUCCESS,
            RESPONSE_DISARMED,
            RESPONSE_ARMED_AWAY,
            RESPONSE_DISARMED
        ]

        # Mocked values for 'time.monotonic'
        mock_times = [
            # Time for initial authentication
            0,

            # Session still valid before RESPONSE_SESSION_DETAILS
            TOKEN_EXPIRATION_TIME - 5,

            # Session still valid before RESPONSE_PARTITION_DETAILS
            TOKEN_EXPIRATION_TIME - 4,

            # Session still valid before RESPONSE_GET_ZONE_DETAILS_SUCCESS
            TOKEN_EXPIRATION_TIME - 3,

            # Session still valid before RESPONSE_DISARMED
            TOKEN_EXPIRATION_TIME - 2,

            # Session expires before RESPONSE_ARMED_AWAY
            TOKEN_EXPIRATION_TIME,

            # Time for session refresh
            TOKEN_EXPIRATION_TIME,

            # Session expires before RESPONSE_DISARMED
            TOKEN_EXPIRATION_TIME * 2,

            # Time for reauthentication
            TOKEN_EXPIRATION_TIME * 2,

            # Session now valid for RESPONSE_DISARMED
            TOKEN_EXPIRATION_TIME * 2 + 1,
        ]

        token_responses = [
            # Successful response for initial authentication
            {"json": HTTP_RESPONSE_TOKEN, "status_code": 200},

            # Successful response for session refresh
            {"json": HTTP_RESPONSE_TOKEN, "status_code": 200},

            # Failed response for refresh
            {"json": HTTP_RESPONSE_REFRESH_TOKEN_FAILED, "status_code": 400},

            # Successful response for reauthentication
            {"json": HTTP_RESPONSE_TOKEN_2, "status_code": 200},
        ]

        with patch("zeep.Client"), patch(
            PATCH_EVAL, side_effect=serialize_responses
        ) as mock_request, patch(
            "time.monotonic", side_effect=mock_times
        ), requests_mock.Mocker(real_http=True) as rm:
            rm.post(TotalConnectClient.TOKEN_ENDPOINT, token_responses)

            client = TotalConnectClient("username", "password", usercodes=None)
            assert mock_request.call_count == 1
            if client.locations:  # force client to fetch them
                pass
            assert mock_request.call_count == 4
            assert client.is_logged_in() is True
            assert client.token == SESSION_ID

            # The session should come up as expired due to the current time.
            # The client refreshes the session and should get the same session id.
            client.locations[LOCATION_INFO_BASIC_NORMAL["LocationID"]].arm(ArmType.AWAY)
            assert mock_request.call_count == 5
            assert client.token == SESSION_ID

            # Check that we made a refresh session request
            refresh_request = rm.request_history[-1]
            assert refresh_request.url == TotalConnectClient.TOKEN_ENDPOINT
            assert "grant_type=refresh_token" in refresh_request.text

            # The session should come up as expired again due to the current time.
            # The session refresh fails so we reauthenticate and get a new session.
            client.locations[LOCATION_INFO_BASIC_NORMAL["LocationID"]].disarm()
            assert mock_request.call_count == 6
            assert client.token == SESSION_ID_2

            # Check that we made an authentication request
            refresh_request = rm.request_history[-1]
            assert refresh_request.url == TotalConnectClient.TOKEN_ENDPOINT
            assert "grant_type=password" in refresh_request.text