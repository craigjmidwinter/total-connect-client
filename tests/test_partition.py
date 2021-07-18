"""Test TotalConnectDevice."""

from copy import deepcopy
from unittest.mock import Mock

from const import PARTITION_DETAILS_1, PARTITION_DISARMED
from partition import TotalConnectPartition
from exceptions import PartialResponseError

import pytest


def tests_partition():
    """Test __init__()."""
    test_partition = TotalConnectPartition(PARTITION_DETAILS_1, None)
    assert test_partition.id == 1

    test_partition.update(PARTITION_DISARMED)
    assert test_partition.arming_state == PARTITION_DISARMED["ArmingState"]

    # remove ArmingState
    data = deepcopy(PARTITION_DETAILS_1)
    del data["ArmingState"]
    with pytest.raises(PartialResponseError):
        test_partition.update(data)

    # no info
    with pytest.raises(PartialResponseError):
        test_partition.update(None)


def tests_str():
    """Test __str__()."""
    test_partition = TotalConnectPartition(PARTITION_DETAILS_1, None)

    data = (
        f"PARTITION {PARTITION_DETAILS_1['PartitionID']} - "
        f"{PARTITION_DETAILS_1['PartitionName']}\n"
        f"  ArmingState: {PARTITION_DETAILS_1['ArmingState']}\n"
    )

    assert str(test_partition) == data


def tests_arm_disarm():
    """Test arm and disarm functions."""
    location = Mock()
    partition = TotalConnectPartition(PARTITION_DETAILS_1, location)

    location.arm_away.return_value = None
    partition.arm_away()

    location.arm_stay.return_value = None
    partition.arm_stay()

    location.arm_stay_instant.return_value = None
    partition.arm_stay_instant()

    location.arm_away_instant.return_value = None
    partition.arm_away_instant()

    location.arm_stay_night.return_value = None
    partition.arm_stay_night()

    location.disarm.return_value = None
    partition.disarm()


def tests_arming_state():
    """Test status functions."""

    partition = TotalConnectPartition(PARTITION_DETAILS_1, None)

    assert partition.is_disarming() is False
    assert partition.is_disarmed() is True
    assert partition.is_arming() is False
    assert partition.is_armed() is False
    assert partition.is_armed_away() is False
    assert partition.is_armed_custom_bypass() is False
    assert partition.is_armed_home() is False
    assert partition.is_armed_night() is False
    assert partition.is_pending() is False
    assert partition.is_triggered_police() is False
    assert partition.is_triggered_fire() is False
    assert partition.is_triggered_gas() is False
    assert partition.is_triggered() is False

    assert partition.get_armed_status() == TotalConnectPartition.DISARMED
