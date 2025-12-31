"""Command-line tool to arm Total Connect alarm systems.

Usage:
    python -m total_connect_client.live.arm username location1=usercode1,location2=usercode2 arm_type

Args:
    username: Total Connect username
    location_usercode_pairs: Comma-separated pairs of location=usercode
    arm_type: Numeric arm type (see ArmType enum)
"""

import getpass
import logging
import sys
from typing import Final, NoReturn

from ..client import TotalConnectClient
from ..const import ArmType

logging.basicConfig(filename="test.log", level=logging.DEBUG)


def usage() -> NoReturn:
    """Print usage instructions."""
    print("usage:  username location1=usercode1,location2=usercode2 arm_type \n")
    print("arm types:")
    for arm_type_enum in list(ArmType):
        print(f"  {arm_type_enum.name}: {arm_type_enum.value}")
    sys.exit()


if len(sys.argv) != 4:
    usage()

USERNAME: Final[str] = sys.argv[1]
USERCODES: Final[dict[str, str]] = dict(x.split("=") for x in sys.argv[2].split(","))
arm_type: Final[ArmType] = ArmType(int(sys.argv[3]))
PASSWORD: Final[str] = getpass.getpass()

TC: Final[TotalConnectClient] = TotalConnectClient(USERNAME, PASSWORD, USERCODES)

for location_id in TC.locations:
    location = TC.locations[location_id]
    location.arm(arm_type)

print(f"Armed: {arm_type}")

sys.exit()
