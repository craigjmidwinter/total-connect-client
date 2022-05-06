"""Test TotalConnectDevice."""

from const import DEVICE_INFO_BASIC_1

from total_connect_client.device import TotalConnectDevice


def tests_init():
    """Test __init__()."""
    test_device = TotalConnectDevice(DEVICE_INFO_BASIC_1)
    assert test_device.deviceid == DEVICE_INFO_BASIC_1["DeviceID"]

    # test with missing flags
    del DEVICE_INFO_BASIC_1["DeviceFlags"]
    test_device = TotalConnectDevice(DEVICE_INFO_BASIC_1)
    assert not test_device.flags
