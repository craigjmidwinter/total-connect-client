"""Test TotalConnectDevice."""

from copy import deepcopy

from partition import TotalConnectPartition

from const import PARTITION_DISARMED

PARTITION_DETAILS = {
    "PartitionID": 1,
    "ArmingState": 0,
    "PartitionName": "Test",
}

def tests_partition():
    """Test __init__()."""
    test_partition = TotalConnectPartition(PARTITION_DETAILS)
    assert test_partition.id == 1

    test_partition.update(PARTITION_DISARMED)
    assert test_partition.arming_state == PARTITION_DISARMED["ArmingState"]

    # remove ArmingState
    data = deepcopy(PARTITION_DETAILS)
    del data["ArmingState"]
    assert test_partition.update(data) is False

    # no info
    assert test_partition.update(None) is False
