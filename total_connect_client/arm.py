"""Test your system from the command line."""

import getpass
import logging
import sys

from .const import ArmType
from .client import TotalConnectClient

logging.basicConfig(filename="test.log", level=logging.DEBUG)


def usage():
    """Print usage instructions."""
    print("usage:  username location1=usercode1,location2=usercode2 arm_type \n")
    print("arm types:")
    for i in list(ArmType):
        print(f"  {i.name}: {i.value}")
    sys.exit()


if len(sys.argv) != 4:
    usage()

USERNAME = sys.argv[1]
USERCODES = dict(x.split("=") for x in sys.argv[2].split(","))
arm_type = ArmType(int(sys.argv[3]))
PASSWORD = getpass.getpass()

TC = TotalConnectClient(USERNAME, PASSWORD, USERCODES)

for location_id in TC.locations:
    TC.locations[location_id].arm(arm_type)

print(f"Armed: {arm_type}")

sys.exit()
