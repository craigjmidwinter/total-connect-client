"""
total_connect_client package

TotalConnectClient is the main class for the Total Connect interface.

Its accessors may return instances of TotalConnectLocation, TotalConnectPartition,
and TotalConnectZone (from .location, .partition, and .zone respectively), but
users of this interface never create those themselves.
"""

from .client import TotalConnectClient

from .const import (
    ARM_TYPE_AWAY,
    ARM_TYPE_STAY,
    ARM_TYPE_STAY_INSTANT,
    ARM_TYPE_AWAY_INSTANT,
    ARM_TYPE_STAY_NIGHT,
)
