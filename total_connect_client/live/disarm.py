"""Test your system from the command line."""

import getpass
import logging
import sys

from total_connect_client.client import TotalConnectClient

logging.basicConfig(filename="test.log", level=logging.DEBUG)

if len(sys.argv) != 3:
    print("usage:  username location1=usercode1,location2=usercode2 \n")
    sys.exit()

USERNAME = sys.argv[1]
USERCODES = dict(x.split("=") for x in sys.argv[2].split(","))
PASSWORD = getpass.getpass()

TC = TotalConnectClient(USERNAME, PASSWORD, USERCODES)

for location_id in TC.locations:
    TC.locations[location_id].disarm()

print("Disarmed.")

sys.exit()
