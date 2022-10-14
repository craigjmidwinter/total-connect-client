"""Test total_connect_client request()."""

import unittest
from unittest.mock import patch
from zeep.exceptions import Fault as ZeepFault

import pytest
from const import (
    MAX_RETRY_ATTEMPTS,
    LOCATION_INFO_BASIC_NORMAL,
    RESPONSE_ARMED_AWAY,
    RESPONSE_AUTHENTICATE,
    RESPONSE_BAD_USER_OR_PASSWORD,
    RESPONSE_CONNECTION_ERROR,
    RESPONSE_DISARMED,
    RESPONSE_FAILED_TO_CONNECT,
    RESPONSE_GET_ZONE_DETAILS_SUCCESS,
    RESPONSE_INVALID_SESSION,
    RESPONSE_PARTITION_DETAILS,
    RESPONSE_SESSION_INITIATED,
    RESPONSE_UNKNOWN,
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
            RESPONSE_AUTHENTICATE,
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
        serialize_responses = [
            RESPONSE_BAD_USER_OR_PASSWORD,
        ]

        with patch("zeep.Client"), patch(
            "zeep.helpers.serialize_object", side_effect=serialize_responses
        ) as mock_request:
            with pytest.raises(AuthenticationError):
                TotalConnectClient("username", "password", usercodes=None)
            assert mock_request.call_count == 1

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
            RESPONSE_AUTHENTICATE,
            RESPONSE_PARTITION_DETAILS,
            RESPONSE_GET_ZONE_DETAILS_SUCCESS,
            RESPONSE_DISARMED,
            RESPONSE_INVALID_SESSION,
            RESPONSE_SESSION_INITIATED,
            RESPONSE_ARMED_AWAY,
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

            assert client.token == RESPONSE_AUTHENTICATE["SessionID"]
            # now try to arm away
            # the invalid session will trigger a new authenticate()...
            # which should result in a new token
            client.locations[LOCATION_INFO_BASIC_NORMAL["LocationID"]].arm(ArmType.AWAY)
            assert mock_request.call_count == 7
            assert client.token == RESPONSE_SESSION_INITIATED["SessionID"]

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
