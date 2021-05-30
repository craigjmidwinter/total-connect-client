"""Total Connect Client."""

class TotalConnectDevice:
    """Device for Total Connect."""

    def __init__(self, info):
        """Initialize device based on DeviceInfoBasic."""

        self.id = info.get("DeviceID")
        self.name = info.get("DeviceName")
        self.class_id = info.get("DeviceClassID")
        self.serial_number = info.get("DeviceSerialNumber")
        self.flags = info.get("DeviceFlags")
        self.security_panel_type_id = info.get("SecurityPanelTypeID")
        self.serial_text = info.get("DeviceSerialText")

    def __str__(self):
        """Return a string that is printable."""
        data = (
            f"DEVICE {self.id} - {self.name}\n"
            f"  ClassID: {self.class_id}\n"
            f"  Security Panel Type ID: {self.security_panel_type_id}\n"
            f"  Serial Number: {self.serial_number}\n"
            f"  Serial Text: P{self.serial_text}\n"
            f"  Device Flags:\n"
        )

        for key, value in self.flags.items():
            data = data + f"    {key}: {value}\n"

        return data + "\n"
