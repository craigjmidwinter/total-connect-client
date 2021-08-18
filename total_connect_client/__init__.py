"""
total_connect_client package

TotalConnectClient is the main class for the Total Connect interface.

Its accessors may return instances of TotalConnectLocation, TotalConnectPartition,
and TotalConnectZone (from .location, .partition, and .zone respectively), but
users of this interface never create those themselves.
"""

from .client import ArmingHelper, TotalConnectClient
from .const import ArmingState, ArmType
