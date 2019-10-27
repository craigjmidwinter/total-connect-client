"""Zone for Total Connect."""


ZONE_STATUS_NORMAL = 0
ZONE_STATUS_BYPASSED = 1
ZONE_STATUS_FAULT = 2
ZONE_STATUS_TAMPER = 8
ZONE_STATUS_TROUBLE_LOW_BATTERY = 72
ZONE_STATUS_TRIGGERED = 256

ZONE_TYPE_SECURITY = 0
ZONE_TYPE_FIRE_SMOKE = 9
ZONE_TYPE_CARBON_MONOXIDE = 14

class TotalConnectZone:
    """TotalConnectZone class."""

    
    def __init__(self, zone):
        """Initialize."""
        self.id = zone.get('ZoneID')
        self.description = zone.get('ZoneDescription')
        self.status = zone.get('ZoneStatus')
        self.partition = zone.get('PartitionID')
        self.zone_type_id = zone.get('ZoneTypeId')

    def update(self, zone):
        """Update the zone."""
        if self.id == zone.get('ZoneID'):
            self.description = zone.get('ZoneDescription')
            self.partition = zone.get('PartitionID')
            self.status = zone.get('ZoneStatus')
        else:
            raise Exception('ZoneID does not match in TotalConnectZone.')

    def __str__(self):
        """Return a string that is printable."""
        text = 'ZoneID: ' + str(self.id) + '\n'
        text = text + 'ZoneDescription: ' + str(self.description) + '\n'
        text = text + 'ZoneStatus: ' + str(self.status) + '\n'
        text = text + 'ZonePartition: ' + str(self.partition) + '\n'
        text = text + 'ZoneTypeID: ' + str(self.zone_type_id) + '\n'
    
        return text