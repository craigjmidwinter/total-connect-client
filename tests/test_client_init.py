"""Test total_connect_client."""

from unittest.mock import patch

import pytest
from const import (
    RESPONSE_AUTHENTICATE,
    RESPONSE_AUTHENTICATE_EMPTY,
    RESPONSE_DISARMED,
    RESPONSE_GET_ZONE_DETAILS_SUCCESS,
    RESPONSE_PARTITION_DETAILS,
)

from tests.const import RESPONSE_PARTITION_DETAILS_TWO
from total_connect_client.client import TotalConnectClient
from total_connect_client.exceptions import TotalConnectError


def tests_init_usercodes_none():
    """Test init with usercodes == None."""
    responses = [
        RESPONSE_AUTHENTICATE,
        RESPONSE_PARTITION_DETAILS,
        RESPONSE_GET_ZONE_DETAILS_SUCCESS,
        RESPONSE_DISARMED,
    ]

    with patch(
        "total_connect_client.client.TotalConnectClient.request", side_effect=responses
    ) as mock_request:
        mock_client = TotalConnectClient("username", "password", usercodes=None)
        assert mock_request.call_count == 1
        if mock_client.locations:  # force client to fetch them
            pass
        assert mock_request.call_count == 4

    assert not mock_client.usercodes


def tests_init_locations_empty():
    """Test init with no locations."""
    responses = [
        RESPONSE_AUTHENTICATE_EMPTY,
    ]

    with patch(
        "total_connect_client.client.TotalConnectClient.request", side_effect=responses
    ) as mock_request, pytest.raises(TotalConnectError):

        mock_client = TotalConnectClient("username", "password", usercodes=None)
        assert mock_client.locations == {}
        assert mock_request.call_count == 1


def tests_init_usercodes_string():
    """Test init with usercodes == a string."""
    responses = [
        RESPONSE_AUTHENTICATE,
        RESPONSE_PARTITION_DETAILS,
        RESPONSE_GET_ZONE_DETAILS_SUCCESS,
        RESPONSE_DISARMED,
    ]

    with patch(
        "total_connect_client.client.TotalConnectClient.request", side_effect=responses
    ):
        with pytest.raises(AttributeError):
            # string is not a valid type for usercodes (only dict)
            TotalConnectClient("username", "password", usercodes="123456")


def tests_init_partitions():
    """Test that partitions populate correctly."""
    # one partition
    responses = [
        RESPONSE_AUTHENTICATE,
        RESPONSE_PARTITION_DETAILS,
        RESPONSE_GET_ZONE_DETAILS_SUCCESS,
        RESPONSE_DISARMED,
    ]

    with patch(
        "total_connect_client.client.TotalConnectClient.request", side_effect=responses
    ) as mock_request:
        mock_client = TotalConnectClient("username", "password", usercodes=None)
        assert mock_request.call_count == 1
        if mock_client.locations:  # force client to fetch them
            pass
        assert mock_request.call_count == 4

        assert len(mock_client.locations["123456"].partitions) == 1

    # two partitions
    responses = [
        RESPONSE_AUTHENTICATE,
        RESPONSE_PARTITION_DETAILS_TWO,
        RESPONSE_GET_ZONE_DETAILS_SUCCESS,
        RESPONSE_DISARMED,
    ]

    with patch(
        "total_connect_client.client.TotalConnectClient.request", side_effect=responses
    ) as mock_request:
        mock_client = TotalConnectClient("username", "password", usercodes=None)
        assert mock_request.call_count == 1
        if mock_client.locations:  # force client to fetch them
            pass
        assert mock_request.call_count == 4

        assert len(mock_client.locations["123456"].partitions) == 2
