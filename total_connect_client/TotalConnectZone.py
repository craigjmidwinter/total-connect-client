"""Zone for Total Connect."""

class TotalConnectZone:
    """TotalConnectZone class."""
    
    def __init__(self, zone):
        """Initialize."""
        self.id = zone.get('ZoneID')
        self.description = zone.get('ZoneDescription')
        self.status = zone.get('ZoneStatus')
        self.partition = zone.get('PartitionID')
