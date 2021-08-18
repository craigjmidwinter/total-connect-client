"""
total_connect_client package

TotalConnectClient is the main class for the Total Connect interface.

Its accessors may return instances of TotalConnectLocation, TotalConnectPartition,
and TotalConnectZone (from .location, .partition, and .zone respectively), but
users of this interface never create those themselves.
"""

from . import client, location, partition, zone, const

TotalConnectClient = client.TotalConnectClient
ArmingHelper = client.ArmingHelper
TotalConnectLocation = location.TotalConnectLocation
TotalConnectPartition = partition.TotalConnectPartition
TotalConnectZone = zone.TotalConnectZone

ZoneStatus = zone.ZoneStatus
ZoneType = zone.ZoneType
ArmingState = const.ArmingState
ArmType = const.ArmType

__all__ = [
    'TotalConnectClient', 'ArmType', 'ArmingState', 'ArmingHelper',
    'ZoneType', 'ZoneStatus',
]
