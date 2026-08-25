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
    """
    panel = TotalConnectDevice(device_list[0])
    panel.unicorn_info = {"DeviceVariant": "home.dv.doorbell"}
    assert panel.is_doorbell() is True
    assert panel.unicorn_info == {"DeviceVariant": "home.dv.doorbell"}


def test_unicorn_info_roundtrips_through_its_own_attribute():
    """The unicorn_info getter returns what its setter stored.

    Regression test: the getter previously returned self._video_info while the
    setter wrote self._unicorn_info, so unicorn data was unreachable through
    the public property and callers silently saw VideoPIR data instead.
    """
    panel = TotalConnectDevice(device_list[0])
    panel.unicorn_info = {"DeviceID": 987654, "DeviceVariant": "home.dv.unicorn"}

    assert panel.unicorn_info == {
        "DeviceID": 987654,
        "DeviceVariant": "home.dv.unicorn",
    }


def test_unicorn_info_and_video_info_are_independent():
    """unicorn_info and video_info are separate stores, not aliases.

    The original bug made unicorn_info an alias of video_info; this pins them
    apart so a future refactor cannot quietly re-merge them.
    """
    panel = TotalConnectDevice(device_list[0])
    panel.video_info = {"DeviceID": 111111, "source": "videopir"}
    panel.unicorn_info = {"DeviceID": 222222, "source": "unicorn"}

    assert panel.video_info == {"DeviceID": 111111, "source": "videopir"}
    assert panel.unicorn_info == {"DeviceID": 222222, "source": "unicorn"}


def test_unicorn_info_defaults_to_empty_dict():
    """A device with no unicorn data reports an empty dict, not video data."""
    panel = TotalConnectDevice(device_list[0])
    panel.video_info = {"DeviceID": 111111, "source": "videopir"}

    assert panel.unicorn_info == {}
