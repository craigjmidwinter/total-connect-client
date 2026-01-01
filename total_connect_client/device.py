"""Total Connect Device."""

import logging
from typing import Any, Final

from .const import PROJECT_URL

LOGGER: Final = logging.getLogger(__name__)

"""
Leverages data collected from the wild and stored in docs/DEVICES.md
(DeviceClassID, PanelType, PanelVariant) gives ["Model", "Model ID"]
"""
MODEL_LOOKUP = {
    (0, 0, 0): ["Unknown model", "Unknown model ID"],
    (1, 2, 1): ["Vista", "21IP"],
    (1, 5, 1): ["Lynx Plus", "L3000"],
    (1, 8, 0): ["Lynx Touch", "L7000"],
    (1, 8, 1): ["Lynx Touch", "L5210"],
    (1, 10, 1): ["Lyric", "LCP500-L"],
    (1, 12, 1): ["ProA7", "Plus"],
    (1, 15, 1): ["Vista", "LTEM-PV/PIV"],
    (7, 0, 0): ["Skybell", "HD"],
    (303, 0, 0): ["Chamerlain", "MyQ"],
}


class TotalConnectDevice:
    """Device class for Total Connect."""

    def __init__(self, info: dict[str, Any]) -> None:
        """Initialize device based on DeviceInfoBasic."""
        self.deviceid = info.get("DeviceID")
        self.name = info.get("DeviceName")
        self.class_id: int = int(info.get("DeviceClassID", 0))
        self.serial_number = info.get("DeviceSerialNumber")
        self.security_panel_type_id = info.get("SecurityPanelTypeID")
        self.serial_text = info.get("DeviceSerialText")
        self._doorbell_info: dict[str, Any] = {}
        self._video_info: dict[str, Any] = {}
        self._unicorn_info: dict[str, Any] = {}

        flags = info.get("DeviceFlags")
        if not flags:
            self.flags = {}
        else:
            self.flags = dict(x.split("=") for x in flags.split(","))

        self._panel_type: int = int(self.flags.get("PanelType", 0))
        self._panel_variant: int = int(self.flags.get("PanelVariant", 0))

    def __str__(self) -> str:  # pragma: no cover
        """Return a string that is printable."""
        data = (
            f"DEVICE {self.deviceid} - {self.name}\n"
            f"  ClassID: {self.class_id}\n"
            f"  Security Panel Type ID: {self.security_panel_type_id}\n"
            f"  Serial Number: {self.serial_number}\n"
            f"  Serial Text: {self.serial_text}\n"
        )

        data = data + "  Device Flags:\n"
        for key, value in self.flags.items():
            data = data + f"    {key}: {value}\n"

        data = data + "  WifiDoorbellInfo:\n"
        for key, value in self._doorbell_info.items():
            data = data + f"    {key}: {value}\n"

        data = data + "  VideoPIRInfo:\n"
        for key, value in self._video_info.items():
            data = data + f"    {key}: {value}\n"

        data = data + "  UnicornInfo:\n"
        for key, value in self._unicorn_info.items():
            data = data + f"    {key}: {value}\n"

        model, model_id = self.model_info()
        data = data + f"  Model: {model}"
        data = data + f"  Model ID: {model_id}"

        return data

    @property
    def doorbell_info(self) -> dict[str, Any]:
        """Return doorbell info."""
        return self._doorbell_info

    @doorbell_info.setter
    def doorbell_info(self, data: dict[str, Any]) -> None:
        """Set values based on WifiDoorBellInfo object."""
        if data:
            self._doorbell_info = data

    def is_doorbell(self) -> bool:
        """Return true if a doorbell."""
        if self._doorbell_info and self._doorbell_info["IsExistingDoorBellUser"] == 1:
            return True

        if self._unicorn_info and self._unicorn_info["DeviceVariant"] == "home.dv.doorbell":
            return True

        return False

    @property
    def video_info(self) -> dict[str, Any]:
        """VideoPIR info."""
        return self._video_info

    @video_info.setter
    def video_info(self, data: dict[str, Any]) -> None:
        """Set values based on VideoPIRInfo object."""
        if data:
            self._video_info = data

    @property
    def unicorn_info(self) -> dict[str, Any]:
        """Unicorn info."""
        return self._video_info

    @unicorn_info.setter
    def unicorn_info(self, data: dict[str, Any]) -> None:
        """Set values based on UnicornInfo object."""
        if data:
            self._unicorn_info = data

    def model_info(self) -> tuple[str, str]:
        """Return device model and ID.

        Used in Home Assistant.
        https://developers.home-assistant.io/blog/2024/07/16/device-info-model-id/

        """
        try:
            model, model_id = MODEL_LOOKUP[(self.class_id, self._panel_type, self._panel_variant)]
        except KeyError:
            LOGGER.warning(
                f"Unknown TotalConnect model info: (DeviceClassID {self.class_id}, "
                f"PanelType {self._panel_type}, PanelVariant {self._panel_variant}). "
                f"Please report at {PROJECT_URL}/issues"
            )
            model, model_id = "Unknown model", "Unknown model ID"

        return model, model_id
