"""Command-line tool to trigger Total Connect alarm systems.

WARNING: This script will trigger actual alarms on all locations!
Only use this for testing purposes in a controlled environment.

Usage:
    python -m total_connect_client.live.trigger username

Args:
    username: Total Connect username
"""

import getpass
import logging
import sys
from typing import Final, NoReturn

from ..client import TotalConnectClient

logging.basicConfig(filename="test.log", level=logging.DEBUG)


def usage() -> NoReturn:
    """Print usage instructions."""
    print("usage:  username\n")
    print("WARNING: This will trigger actual alarms!")
    sys.exit()


def confirm_trigger() -> None:
    """Confirm that user really wants to trigger alarms."""
    print("WARNING: This will trigger actual alarms on ALL your locations!")
    print("This should only be used for testing purposes.")
    response = input("Are you sure you want to continue? (yes/NO): ")
    if response.lower() != "yes":
        print("Operation cancelled.")
        sys.exit(0)


if len(sys.argv) != 2:
    usage()

USERNAME: Final[str] = sys.argv[1]
PASSWORD: Final[str] = getpass.getpass()

TC: Final[TotalConnectClient] = TotalConnectClient(USERNAME, PASSWORD)

print("Authenticated with Total Connect")
confirm_trigger()

for location_id in TC.locations:
    location = TC.locations[location_id]
    print(f"Attempting to trigger location {location_id}")
    try:
        location.trigger()
        print(f"Successfully triggered alarm for location {location_id}")
    except Exception as e:
        print(f"Failed to trigger location {location_id}: {e}")
        logging.exception("Failed to trigger alarm for location %s", location_id)

print("Trigger operations completed. Check test.log for details.")
sys.exit()
