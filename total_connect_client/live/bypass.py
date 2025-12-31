"""Test zone bypass functionality from the command line."""

import getpass
import logging
import sys
import time

from ..client import TotalConnectClient

logging.basicConfig(filename="test.log", level=logging.DEBUG)


def usage():
    """Print usage instructions."""
    print("usage:  python -m total_connect_client.live.bypass username location1=usercode1,location2=usercode2\n")
    print("This script will:")
    print("1. Try to bypass all faulted zones")
    print("2. Wait for 10 seconds")
    print("3. Try to clear all bypassed zones")
    sys.exit()


if len(sys.argv) != 3:
    usage()

USERNAME = sys.argv[1]
USERCODES = dict(x.split("=") for x in sys.argv[2].split(","))
PASSWORD = getpass.getpass()

TC = TotalConnectClient(USERNAME, PASSWORD, USERCODES)

for location_id in TC.locations:
    location = TC.locations[location_id]
    print(f"\n=== Testing bypass for location {location_id} ({location.location_name}) ===")
    
    # Get current zone status
    location.get_zone_details()
    
    print(f"Found {len(location.zones)} zones")
    
    # Show faulted zones
    faulted_zones = []
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
        
        # Wait 10 seconds
        print("Waiting 10 seconds...")
        time.sleep(10)
        
        # Refresh zone status
        location.get_zone_details()
        
        # Show bypassed zones
        bypassed_zones = []
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