"""Test TotalConnectDevice."""

from const import REST_RESULT_SESSION_DETAILS, SECURITY_DEVICE_ID

from total_connect_client.device import TotalConnectDevice

device_list = REST_RESULT_SESSION_DETAILS["SessionDetailsResult"]["Locations"][0][
    "DeviceList"
]
# [0] is a ProA7 panel
# [1] is the built-in camera
# [2] is a Skybell doorbell


def tests_panel():
    """Test an alarm panel."""
    panel = TotalConnectDevice(device_list[0])
    assert panel.deviceid == SECURITY_DEVICE_ID
    assert panel.is_doorbell() is False
