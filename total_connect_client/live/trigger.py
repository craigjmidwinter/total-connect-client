"""Test your system from the command line."""

import getpass
import logging
import sys

from ..client import TotalConnectClient

logging.basicConfig(filename="test.log", level=logging.DEBUG)


def usage():
    """Print usage instructions."""
    print("usage:  username\n")
    sys.exit()


if len(sys.argv) != 2:
    usage()

USERNAME = sys.argv[1]
PASSWORD = getpass.getpass()

TC = TotalConnectClient(USERNAME, PASSWORD)

print("authenticated with Total Connect")
for location_id in TC.locations:
    print(f"attempting to trigger location {location_id}")
    TC.locations[location_id].trigger()

sys.exit()
