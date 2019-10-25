"""Location for Total Connect."""


class TotalConnectLocation:
    """TotalConnectLocation class."""

    def __init__(self, location):
        """Initialize."""
        self.location_id = location.get('LocationID')
        self.location_name = location.get('LocationName')
        self.security_device_id = location.get('SecurityDeviceID')
        self.ac_loss = None
        self.low_battery = None
        self.is_cover_tampered = None
        self.zones = {}

    def __str__(self):
        """Return a texting that is printable."""
        text = 'LocationID: ' + str(self.location_id) + '\n'
        text = text + 'LocationName: ' + str(self.location_name) + '\n'
        text = text + 'SecurityDeviceID: ' + str(self.security_device_id) + '\n'
        text = text + 'AcLoss: ' + str(self.ac_loss) + '\n'
        text = text + 'LowBattery: ' + str(self.low_battery) + '\n'
        text = text + 'IsCoverTampered: ' + str(self.is_cover_tampered) + '\n'

        return text