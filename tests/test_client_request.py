"""Test total_connect_client request()."""

import unittest
from unittest.mock import patch

import requests
from zeep.exceptions import Fault as ZeepFault
from oauthlib.oauth2 import OAuth2Error, TokenExpiredError

import pytest
import requests_mock
from const import (
    LOCATION_INFO_BASIC_NORMAL,
    RESPONSE_ARMED_AWAY,
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
    SESSION_ID,
    SESSION_ID_2,
)

from total_connect_client.const import ArmType, AUTH_TOKEN_ENDPOINT, _ResultCode
from total_connect_client.client import TotalConnectClient
from total_connect_client.exceptions import (
    AuthenticationError,
    BadResultCodeError,
    RetryableTotalConnectError,
    ServiceUnavailable
)


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
            RESPONSE_PARTITION_DETAILS,
            RESPONSE_GET_ZONE_DETAILS_SUCCESS,
            RESPONSE_DISARMED,
        ]

        with patch("zeep.Client"), patch(
            "zeep.helpers.serialize_object", side_effect=serialize_responses
        ):
            client = TotalConnectClient("username", "password", usercodes=None)
            if client.locations:  # force client to fetch them
                pass
            assert client.is_logged_in() is True

    def tests_request_init_bad_user_or_password(self):
        """Test init sequence with a bad password."""
        with requests_mock.Mocker(real_http=True) as rm:
            rm.post(
                AUTH_TOKEN_ENDPOINT,
                json=HTTP_RESPONSE_BAD_USER_OR_PASSWORD,
                status_code=403
            )
            with pytest.raises(AuthenticationError):
                TotalConnectClient("username", "password", usercodes=None)

    def tests_request_init_failed_to_connect(self):
        """Test init sequence when it fails to connect."""
        serialize_responses = [
            RESPONSE_FAILED_TO_CONNECT for x in range(TotalConnectClient.MAX_RETRY_ATTEMPTS)
        ]

        # Patch the SOAP client so that it raises a connection error
        with patch("zeep.Client"), patch("time.sleep", autospec=True), patch(
            "zeep.helpers.serialize_object", side_effect=serialize_responses
        ) as mock_request:
            client = TotalConnectClient(
                "username", "password", usercodes=None, retry_delay=0
            )

            # Force client to fetch all locations
            with pytest.raises(RetryableTotalConnectError) as exc:
                if client.locations:
                    pass

            assert mock_request.call_count == TotalConnectClient.MAX_RETRY_ATTEMPTS
            assert "failed to connect with panel" in str(exc.value)

    def tests_request_connection_error(self):
        """Test a connection error."""
        serialize_responses = [
            RESPONSE_CONNECTION_ERROR for x in range(TotalConnectClient.MAX_RETRY_ATTEMPTS)
        ]

        # Patch the SOAP client so that it raises a connection error
        with patch("zeep.Client"), patch("time.sleep", autospec=True), patch(
            "zeep.helpers.serialize_object", side_effect=serialize_responses
        ) as mock_request:
            client = TotalConnectClient(
                "username", "password", usercodes=None, retry_delay=0
            )

            # Make a SOAP request
            with pytest.raises(RetryableTotalConnectError) as exc:
                client.request("Test", (client.token,))

            assert mock_request.call_count == TotalConnectClient.MAX_RETRY_ATTEMPTS
            assert "connection error" in str(exc.value)

    def tests_request_zeep_error(self):
        """Test a Zeep error."""

        # Patch the SOAP client so that it raises an internal exception
        serialize_responses = [ZeepFault("test") for x in range(TotalConnectClient.MAX_RETRY_ATTEMPTS)]
        with patch("zeep.Client"), patch("time.sleep", autospec=True), patch(
            "zeep.helpers.serialize_object", side_effect=serialize_responses
        ) as mock_request:
            client = TotalConnectClient(
                "username", "password", usercodes=None, retry_delay=0
            )

            # Make a SOAP request
            with pytest.raises(ServiceUnavailable):
                client.request("Test", (client.token,))

            # Check that the call was tried the correct number of times
            assert mock_request.call_count == TotalConnectClient.MAX_RETRY_ATTEMPTS

    def tests_http_retryable_error(self):
        """Test a retryable API error recieved via HTTP."""

        client = TotalConnectClient(
            "username", "password", usercodes=None, retry_delay=0
        )

        with requests_mock.Mocker() as rm:
            mock_request = rm.get(
                "https://api/test",
                json=RESPONSE_CONNECTION_ERROR,
                status_code=502
            )

            # Make an HTTP Request and check that we get the correct exception from the
            # library.
            with pytest.raises(RetryableTotalConnectError):
                client.http_request(
                    endpoint="https://api/test",
                    method="GET"
                )

            # Check that the call was tried the correct number of times
            assert mock_request.call_count == TotalConnectClient.MAX_RETRY_ATTEMPTS

    def tests_http_request_error(self):
        """Test an HTTP Error."""

        client = TotalConnectClient(
            "username", "password", usercodes=None, retry_delay=0
        )

        with requests_mock.Mocker() as rm:
            mock_request = rm.get("https://api/test", exc=requests.RequestException)

            # Make an HTTP Request and check that we get the correct exception from the
            # library.
            with pytest.raises(ServiceUnavailable):
                client.http_request(
                    endpoint="https://api/test",
                    method="GET"
                )

            # Check that the call was tried the correct number of times
            assert mock_request.call_count == TotalConnectClient.MAX_RETRY_ATTEMPTS

    def tests_request_invalid_session(self):
        """Test an invalid session, which is when the session times out."""
        # First responses set up 'normal' session
        # Call to client.arm_away() will first get an invalid session,
        # which will trigger client.authenticate() before completing the arm_away()
        serialize_responses = [
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
            "zeep.helpers.serialize_object", side_effect=serialize_responses
        ), requests_mock.Mocker(real_http=True) as rm:
            rm.post(AUTH_TOKEN_ENDPOINT, token_responses)
            client = TotalConnectClient("username", "password", usercodes=None)
            if client.locations:  # force client to fetch them
                pass
            assert client.is_logged_in() is True

            assert client.token == SESSION_ID
            # now try to arm away
            # the invalid session will trigger a new authenticate()...
            # which should result in a new token
            client.locations[LOCATION_INFO_BASIC_NORMAL["LocationID"]].arm(ArmType.AWAY)
            assert client.token == SESSION_ID_2

    def tests_request_unknown_result_code(self):
        """Test an unknown result code."""
        with pytest.raises(BadResultCodeError):
            _ResultCode.from_response(RESPONSE_UNKNOWN)


    def tests_empty_response_code(self):
        """Test an empty response code."""
        # see issue #228
        with pytest.raises(ServiceUnavailable):
            _ResultCode.from_response(None)

    def tests_refresh_session(self):
        """Test various scenarious around session refreshing. First the session expires and is
        successfully refreshed, then the session expires and the refresh fails, forcing a full
        reauthentication"""
        # First responses set up 'normal' session
        # Call to client.arm_away() will first require a session refresh
        # Call to client.disarm() will first require a session refresh
        serialize_responses = [
            RESPONSE_PARTITION_DETAILS,
            RESPONSE_GET_ZONE_DETAILS_SUCCESS,
            RESPONSE_DISARMED,
            RESPONSE_ARMED_AWAY,
            RESPONSE_DISARMED
        ]

        with patch("zeep.Client"), patch(
            "zeep.helpers.serialize_object", side_effect=serialize_responses
        ), patch(
            "total_connect_client.client.LegacyApplicationClient",
            autospec=True
        ) as mock_oauth_client_class, patch(
            "total_connect_client.client.OAuth2Session",
            autospec=True
        ) as mock_oauth_session_class:
            mock_oauth_client = mock_oauth_client_class.return_value
            mock_oauth_session = mock_oauth_session_class.return_value

            # Pass HTTP requests through to our mocked requests library
            mock_oauth_session.request.side_effect = requests.request

            # Test initial authentication
            mock_oauth_session.access_token = HTTP_RESPONSE_TOKEN["access_token"].encode()
            client = TotalConnectClient("username", "password", usercodes=None)
            if client.locations:  # force client to fetch them
                pass
            assert client.is_logged_in() is True
            assert client.token == SESSION_ID
            mock_oauth_session.fetch_token.assert_called_once()
            mock_oauth_session.refresh_token.reset_mock()
            mock_oauth_session.fetch_token.reset_mock()

            # The session should come up as expired due to the TokenExpiredError.
            # The client refreshes the session and should get the same session id.
            mock_oauth_client.add_token.side_effect = [TokenExpiredError, None]
            client.locations[LOCATION_INFO_BASIC_NORMAL["LocationID"]].arm(ArmType.AWAY)
            assert client.token == SESSION_ID

            # Check that we refreshed but did not reauthenticate
            mock_oauth_session.refresh_token.assert_called_once()
            mock_oauth_session.fetch_token.assert_not_called()
            mock_oauth_session.refresh_token.reset_mock()
            mock_oauth_session.fetch_token.reset_mock()

            # The session should come up as expired again due to the TokenExpiredError.
            # The session refresh fails so we reauthenticate and get a new session.
            mock_oauth_session.refresh_token.side_effect = OAuth2Error
            mock_oauth_client.add_token.side_effect = [TokenExpiredError, None]
            mock_oauth_session.access_token = HTTP_RESPONSE_TOKEN_2["access_token"].encode()
            client.locations[LOCATION_INFO_BASIC_NORMAL["LocationID"]].disarm()
            assert client.token == SESSION_ID_2

            # Check that we refreshed and reauthenticated
            mock_oauth_session.refresh_token.assert_called_once()
            mock_oauth_session.fetch_token.assert_called_once()
