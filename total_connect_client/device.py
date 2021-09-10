"""Total Connect Device."""


class TotalConnectDevice:
    """Device class for Total Connect."""

    def __init__(self, info):
        """Initialize device based on DeviceInfoBasic."""
        self.deviceid = info.get("DeviceID")
        self.name = info.get("DeviceName")
        self.class_id = info.get("DeviceClassID")
        self.serial_number = info.get("DeviceSerialNumber")
        self.security_panel_type_id = info.get("SecurityPanelTypeID")
        self.serial_text = info.get("DeviceSerialText")

        flags = info.get("DeviceFlags")
        if flags is None:
            self.flags = {}
        else:
            self.flags = dict(x.split("=") for x in flags.split(","))

    def __str__(self):
        """Return a string that is printable."""
        data = (
            f"DEVICE {self.deviceid} - {self.name}\n"
            f"  ClassID: {self.class_id}\n"
            f"  Security Panel Type ID: {self.security_panel_type_id}\n"
            f"  Serial Number: {self.serial_number}\n"
            f"  Serial Text: {self.serial_text}\n"
            f"  Device Flags:\n"
        )

        for key, value in self.flags.items():
            data = data + f"    {key}: {value}\n"

        return data
