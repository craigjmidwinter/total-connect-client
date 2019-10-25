"""Zone for Total Connect."""

class TotalConnectZone:
    """TotalConnectZone class."""

        # ZoneTypeId
        # 0 = security
        # 9 = fire
        #14 = carbon monoxide / gas

    
    def __init__(self, zone):
        """Initialize."""
        self.id = zone.get('ZoneID')
        self.description = None
        self.status = zone.get('ZoneStatus')
        self.partition = zone.get('PartitionID')
        self.zone_type_id = zone.get('ZoneTypeId')

    def update(self, zone):
        """Update the zone."""
        if self.id == zone.get('ZoneID'):
            self.description = zone.get('ZoneDescription')
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