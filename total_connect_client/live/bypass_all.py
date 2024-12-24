"""Sync system from the command line."""

import getpass
import logging
import sys
import time

from total_connect_client.client import TotalConnectClient

logging.basicConfig(filename="test.log", level=logging.DEBUG)

if len(sys.argv) != 3:
    print("usage:  username location1=usercode1,location2=usercode2 \n")
    sys.exit()

USERNAME = sys.argv[1]
USERCODES = dict(x.split("=") for x in sys.argv[2].split(","))
PASSWORD = getpass.getpass()

TC = TotalConnectClient(USERNAME, PASSWORD, USERCODES)

print("Attempt to bypass all zones.")
for location_id in TC.locations:
    print(f"Bypassing all for location {location_id}")
    TC.locations[location_id].zone_bypass_all()

print("All zones bypassed.  Please verify zones are bypassed as expected.")
print("Bypass will be cleared in 2 minutes.")
time.sleep(60)
print("Bypass will be cleared in 1 minute.")
time.sleep(60)

print("Clearing bypasses.")
for location_id in TC.locations:
    print(f"Clearing bypassing all for location {location_id}")
    TC.locations[location_id].clear_bypass()

print("Cleared zone bypasses.  Please verify zones are faulted/open as expected.")

print("\n\nThanks for helping test.  Please report results on Github.\n\n")

sys.exit()
