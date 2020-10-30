"""Test your system from the command line."""

import logging
import sys

import TotalConnectClient

logging.basicConfig(filename="test.log", level=logging.DEBUG)

if len(sys.argv) != 4:
    print(
        "usage:  python3 test.py username password "
        "location1=usercode1,location2=usercode2 \n"
    )
    sys.exit()


USERNAME = sys.argv[1]
PASSWORD = sys.argv[2]
USERCODES = dict(x.split("=") for x in sys.argv[3].split(","))

print(f"usercodes: {USERCODES}")

TC = TotalConnectClient.TotalConnectClient(USERNAME, PASSWORD, USERCODES)

for location_id in TC.locations:

    if str(location_id) in USERCODES:
        code = USERCODES[str(location_id)]
    else:
        print(f"location {location_id} not found in locations.")
        code = TotalConnectClient.DEFAULT_USERCODE

    if TC.locations[location_id].set_usercode(code):
        print(f"Usercode {code} valid for location {location_id}.")
    else:
        print(f"Usercode {code} invalid for location {location_id}.")

sys.exit()
