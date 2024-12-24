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

print("Attempt to sync.")
for location_id in TC.locations:
    TC.locations[location_id].sync_panel()

print("Immediately request job status.")
for location_id in TC.locations:
    TC.locations[location_id].get_sync_status()

print("Wait 2 minutes then ask for status again.")
time.sleep(120)
for location_id in TC.locations:
    TC.locations[location_id].get_sync_status()

sys.exit()
