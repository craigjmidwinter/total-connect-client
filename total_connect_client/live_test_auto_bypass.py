"""Test your system from the command line."""

import logging
import sys
from pprint import pprint

import TotalConnectClient

logging.basicConfig(filename="test.log", level=logging.DEBUG)

if len(sys.argv) != 3:
    print("usage:  python3 test.py username password\n")
    sys.exit()


USERNAME = sys.argv[1]
PASSWORD = sys.argv[2]

TC = TotalConnectClient.TotalConnectClient(USERNAME, PASSWORD)

location_id = next(iter(TC.locations))

print("auto_bypass_low_battery: " + str(TC.auto_bypass_low_battery))

print("\n\n\n")

print("--- panel meta data ---")
meta_data = TC.get_panel_meta_data(location_id)
pprint(meta_data)

print("\n\n\n")

print(TC.locations[location_id])

for z in TC.locations[location_id].zones:
    print(TC.locations[location_id].zones[z])
