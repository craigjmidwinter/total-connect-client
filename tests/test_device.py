"""Test TotalConnectDevice."""

from const import REST_RESULT_SESSION_DETAILS, SECURITY_DEVICE_ID

from total_connect_client.device import TotalConnectDevice

device_list = REST_RESULT_SESSION_DETAILS["SessionDetailsResult"]["Locations"][0]["DeviceList"]
# [0] is a ProA7 panel
# [1] is the built-in camera
# [2] is a Skybell doorbell


def tests_panel():
    """Test an alarm panel."""
    panel = TotalConnectDevice(device_list[0])
    assert panel.deviceid == SECURITY_DEVICE_ID
    assert panel.is_doorbell() is False


def tests_model():
    """Test model info."""
    panel = TotalConnectDevice(device_list[0])
    model, model_id = panel.model_info()
    assert model == "ProA7"
    assert model_id == "Plus"

    # unknown info
    panel.class_id = 666
    model, model_id = panel.model_info()
    assert model == "Unknown model"
    assert model_id == "Unknown model ID"


def test_video_info_setter_and_getter_round_trip():
    """video_info can be set (e.g. from a VideoPIRInfo payload) and read back."""
    panel = TotalConnectDevice(device_list[0])
    payload = {"SomeKey": "value"}
    panel.video_info = payload
    assert panel.video_info == payload


def test_doorbell_info_setter_and_getter_round_trip():
    """doorbell_info can be set (e.g. from a WiFiDoorBellInfo payload) and read back."""
    panel = TotalConnectDevice(device_list[0])
    payload = {"IsExistingDoorBellUser": 1}
    panel.doorbell_info = payload
    assert panel.doorbell_info == payload


def test_doorbell_info_setter_ignores_falsy_data():
    """Setting doorbell_info to a falsy value (e.g. {}) does not clear existing info."""
    panel = TotalConnectDevice(device_list[0])
    panel.doorbell_info = {"IsExistingDoorBellUser": 1}
    panel.doorbell_info = {}
    assert panel.doorbell_info == {"IsExistingDoorBellUser": 1}


def test_is_doorbell_true_when_doorbell_info_flags_existing_user():
    """is_doorbell() is True once doorbell_info reports an existing doorbell user."""
    panel = TotalConnectDevice(device_list[0])
    panel.doorbell_info = {"IsExistingDoorBellUser": 1}
    assert panel.is_doorbell() is True


def test_is_doorbell_true_when_unicorn_variant_is_doorbell():
    """is_doorbell() is also True for a Unicorn-class device whose DeviceVariant marks
    it as a doorbell.

    NOTE: this only exercises the unicorn_info *setter* and is_doorbell()'s own
    (correct) use of self._unicorn_info. It deliberately does not assert on the
    unicorn_info *property getter*, which has a bug: it returns
    self._video_info instead of self._unicorn_info. Asserting on it here would
    lock that bug in place.
    """
    panel = TotalConnectDevice(device_list[0])
    panel.unicorn_info = {"DeviceVariant": "home.dv.doorbell"}
    assert panel.is_doorbell() is True
