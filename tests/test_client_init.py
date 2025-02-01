"""Test total_connect_client."""

from unittest.mock import patch

import pytest
import requests_mock
from const import (
    HTTP_RESPONSE_SESSION_DETAILS_EMPTY,
    RESPONSE_DISARMED,
    RESPONSE_GET_ZONE_DETAILS_SUCCESS,
    RESPONSE_PARTITION_DETAILS,
    RESPONSE_PARTITION_DETAILS_TWO
)

from total_connect_client.client import TotalConnectClient
from total_connect_client.const import HTTP_API_SESSION_DETAILS_ENDPOINT
from total_connect_client.exceptions import TotalConnectError


def tests_init_usercodes_none():
    """Test init with usercodes == None."""
    responses = [
        RESPONSE_PARTITION_DETAILS,
        RESPONSE_GET_ZONE_DETAILS_SUCCESS,
        RESPONSE_DISARMED,
    ]

    with patch(
        "total_connect_client.client.TotalConnectClient.request", side_effect=responses
    ):
        mock_client = TotalConnectClient("username", "password", usercodes=None)

    assert not mock_client.usercodes


def tests_init_locations_empty():
    """Test init with no locations."""
    with requests_mock.Mocker(real_http=True) as rm, pytest.raises(TotalConnectError):
        rm.get(
            HTTP_API_SESSION_DETAILS_ENDPOINT,
            json=HTTP_RESPONSE_SESSION_DETAILS_EMPTY,
            status_code=200
        )

        mock_client = TotalConnectClient("username", "password", usercodes=None)
        assert mock_client.locations == {}


def tests_init_usercodes_string():
    """Test init with usercodes == a string."""
    responses = [
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
        RESPONSE_PARTITION_DETAILS,
        RESPONSE_GET_ZONE_DETAILS_SUCCESS,
        RESPONSE_DISARMED,
    ]

    with patch(
        "total_connect_client.client.TotalConnectClient.request", side_effect=responses
    ):
        mock_client = TotalConnectClient("username", "password", usercodes=None)
        if mock_client.locations:  # force client to fetch them
            pass

        assert len(mock_client.locations["123456"].partitions) == 1

    # two partitions
    responses = [
        RESPONSE_PARTITION_DETAILS_TWO,
        RESPONSE_GET_ZONE_DETAILS_SUCCESS,
        RESPONSE_DISARMED,
    ]

    with patch(
        "total_connect_client.client.TotalConnectClient.request", side_effect=responses
    ):
        mock_client = TotalConnectClient("username", "password", usercodes=None)
        if mock_client.locations:  # force client to fetch them
            pass

        assert len(mock_client.locations["123456"].partitions) == 2
