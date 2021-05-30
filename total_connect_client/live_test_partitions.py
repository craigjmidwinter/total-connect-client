"""Test your system from the command line."""

import logging
import sys
from pprint import pprint

import TotalConnectClient

logging.basicConfig(filename="test.log", level=logging.DEBUG)

if len(sys.argv) != 5:
    print(
        "usage:  python3 test.py username password LocationID DeviceID\n"
    )
    sys.exit()

USERNAME = sys.argv[1]
PASSWORD = sys.argv[2]
LOCATION = sys.argv[3]
DEVICE_ID = sys.argv[4]

TC = TotalConnectClient.TotalConnectClient(USERNAME, PASSWORD)

print("\n\n\nGetPartitionsDetails without partition number\n\n\n")

result = TC.request(f"GetPartitionsDetails(self.token, {LOCATION}, {DEVICE_ID})")

pprint(result)
