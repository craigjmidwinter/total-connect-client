class TotalConnectZone:
    
    def __init__(self, zone):
        """"""
        self.id = zone.get('ZoneID')
        self.description = zone.get('ZoneDescription')
        self.status = zone.get('ZoneStatus')
        self.partition = zone.get('PartitionID')
