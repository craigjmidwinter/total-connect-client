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

TC = TotalConnectClient.TotalConnectClient(USERNAME, PASSWORD, USERCODES)

for location_id in TC.locations:
    if TC.disarm(location_id):
        print("Disarm success.")
    else:
        print("Disarm failure.  Check logs.")

sys.exit()
