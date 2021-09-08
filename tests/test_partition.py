"""Test TotalConnectDevice."""

from copy import deepcopy
from unittest.mock import Mock

import pytest
from const import PARTITION_DETAILS_1, PARTITION_DISARMED

from total_connect_client.client import ArmingHelper
from total_connect_client.exceptions import PartialResponseError, TotalConnectError
from total_connect_client.partition import TotalConnectPartition


def tests_partition():
    """Test __init__()."""
    test_partition = TotalConnectPartition(PARTITION_DETAILS_1, None)
    assert test_partition.id == 1

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


def tests_str():
    """Test __str__()."""
    test_partition = TotalConnectPartition(PARTITION_DETAILS_1, None)

    data = (
        f"PARTITION {PARTITION_DETAILS_1['PartitionID']} - "
        f"{PARTITION_DETAILS_1['PartitionName']}\n"
        f"  ArmingState.DISARMED\n"
    )

    assert str(test_partition) == data


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
