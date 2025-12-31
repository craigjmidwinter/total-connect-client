"""Command-line tool to test zone bypass functionality.

This script tests the complete bypass workflow:
1. Identifies faulted zones in the alarm system
2. Attempts to bypass all faulted zones
3. Waits 10 seconds for the system to process
4. Attempts to clear all bypassed zones

Usage:
    python -m total_connect_client.live.bypass username location1=usercode1,location2=usercode2

Args:
    username: Total Connect username
    location_usercode_pairs: Comma-separated pairs of location=usercode
"""

import getpass
import logging
import sys
import time
from typing import Final, NoReturn

from ..client import TotalConnectClient

logging.basicConfig(filename="test.log", level=logging.DEBUG)

BYPASS_WAIT_TIME: Final[int] = 10


def usage() -> NoReturn:
    """Print usage instructions."""
    print("usage:  python -m total_connect_client.live.bypass username location1=usercode1,location2=usercode2\n")
    print("This script will:")
    print("1. Try to bypass all faulted zones")
    print("2. Wait for 10 seconds")
    print("3. Try to clear all bypassed zones")
    sys.exit()


if len(sys.argv) != 3:
    usage()

USERNAME: Final[str] = sys.argv[1]
USERCODES: Final[dict[str, str]] = dict(x.split("=") for x in sys.argv[2].split(","))
PASSWORD: Final[str] = getpass.getpass()

TC: Final[TotalConnectClient] = TotalConnectClient(USERNAME, PASSWORD, USERCODES)

for location_id in TC.locations:
    location = TC.locations[location_id]
    print(f"\n=== Testing bypass for location {location_id} ({location.location_name}) ===")
    
    # Get current zone status
    location.get_zone_details()
    
    print(f"Found {len(location.zones)} zones")
    
    # Show faulted zones
    faulted_zones: list[int] = []
    for zone_id, zone in location.zones.items():
        if zone.is_faulted():
            faulted_zones.append(zone_id)
            print(f"Zone {zone_id} ({zone.description}) is faulted")
    
    if not faulted_zones:
        print("No faulted zones found. Cannot test bypass functionality.")
        continue
    
    print(f"\nAttempting to bypass {len(faulted_zones)} faulted zones: {faulted_zones}")
    
    try:
        # Bypass all faulted zones
        location.zone_bypass_all()
        print("Successfully initiated bypass for all faulted zones")
        
        # Wait for system to process
        print(f"Waiting {BYPASS_WAIT_TIME} seconds...")
        time.sleep(BYPASS_WAIT_TIME)
        
        # Refresh zone status
        location.get_zone_details()
        
        # Show bypassed zones
        bypassed_zones: list[int] = []
        for zone_id, zone in location.zones.items():
            if zone.is_bypassed():
                bypassed_zones.append(zone_id)
                print(f"Zone {zone_id} ({zone.description}) is bypassed")
        
        print(f"\nAttempting to clear bypass for {len(bypassed_zones)} bypassed zones")
        
        # Clear all bypassed zones
        location.clear_bypass()
        print("Successfully cleared all bypassed zones")
        
    except Exception as e:
        print(f"Error during bypass test: {e}")
        logging.exception("Error during bypass test")

print("\nBypass test completed. Check test.log for detailed debug information.")