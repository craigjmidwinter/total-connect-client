"""Test TotalConnectDevice."""

from copy import deepcopy
from unittest.mock import Mock

import pytest
from const import PARTITION_DETAILS_1, PARTITION_DISARMED

from total_connect_client.client import ArmingHelper
from total_connect_client.const import ArmingState
from total_connect_client.exceptions import PartialResponseError, TotalConnectError
from total_connect_client.partition import TotalConnectPartition


def tests_partition():
    """Test __init__()."""
    test_partition = TotalConnectPartition(PARTITION_DETAILS_1, None)
    assert test_partition.partitionid == 1

    test_partition._update(PARTITION_DISARMED)
    assert test_partition.arming_state.value == PARTITION_DISARMED["ArmingState"]

    unknown = deepcopy(PARTITION_DISARMED)
    unknown["ArmingState"] = "999999999"
    with pytest.raises(TotalConnectError):
        test_partition._update(unknown)

    # remove ArmingState
    data = deepcopy(PARTITION_DETAILS_1)
    del data["ArmingState"]
    with pytest.raises(PartialResponseError):
        test_partition._update(data)

    # no info
    with pytest.raises(PartialResponseError):
        test_partition._update(None)


def tests_arm_disarm():
    """Test arm and disarm functions."""
    location = Mock()
    partition = TotalConnectPartition(PARTITION_DETAILS_1, location)

    location.arm_away.return_value = None
    ArmingHelper(partition).arm_away()

    location.arm_stay.return_value = None
    ArmingHelper(partition).arm_stay()

    location.arm_stay_instant.return_value = None
    ArmingHelper(partition).arm_stay_instant()

    location.arm_away_instant.return_value = None
    ArmingHelper(partition).arm_away_instant()

    location.arm_stay_night.return_value = None
    ArmingHelper(partition).arm_stay_night()

    location.disarm.return_value = None
    ArmingHelper(partition).disarm()


def tests_arming_state():
    """Test status functions."""

    partition = TotalConnectPartition(PARTITION_DETAILS_1, None)

    assert partition.arming_state.is_disarming() is False
    assert partition.arming_state.is_disarmed() is True
    assert partition.arming_state.is_arming() is False
    assert partition.arming_state.is_armed() is False
    assert partition.arming_state.is_armed_away() is False
    assert partition.arming_state.is_armed_custom_bypass() is False
    assert partition.arming_state.is_armed_home() is False
    assert partition.arming_state.is_armed_night() is False
    assert partition.arming_state.is_pending() is False
    assert partition.arming_state.is_triggered_police() is False
    assert partition.arming_state.is_triggered_fire() is False
    assert partition.arming_state.is_triggered_gas() is False
    assert partition.arming_state.is_triggered() is False


def tests_proa7_states():
    """Test ProA7 status functions."""

    partition_info = {
        "PartitionID": 1,
        "PartitionName": "Test1",
    }

    armed_stay = [
        ArmingState.ARMED_STAY_PROA7,
        ArmingState.ARMED_STAY_BYPASS_PROA7,
        ArmingState.ARMED_STAY_INSTANT_PROA7,
        ArmingState.ARMED_STAY_INSTANT_BYPASS_PROA7
    ]

    armed_night = [
        ArmingState.ARMED_STAY_NIGHT_BYPASS_PROA7,
        ArmingState.ARMED_STAY_NIGHT_INSTANT_PROA7,
        ArmingState.ARMED_STAY_NIGHT_INSTANT_BYPASS_PROA7,
    ]

    for state in armed_stay:
        partition_info["ArmingState"] = state
        partition = TotalConnectPartition(partition_info, None)
        assert partition.arming_state.is_armed() is True
        assert partition.arming_state.is_armed_home() is True
        assert partition.arming_state.is_armed_night() is False
        assert partition.arming_state.is_armed_away() is False

    for state in armed_night:
        partition_info["ArmingState"] = state
        partition = TotalConnectPartition(partition_info, None)
        assert partition.arming_state.is_armed() is True
        assert partition.arming_state.is_armed_home() is True
        assert partition.arming_state.is_armed_night() is True
        assert partition.arming_state.is_armed_away() is False
