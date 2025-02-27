"""Test your system from the command line."""

import getpass
import logging
import sys
from time import sleep

from total_connect_client.client import TotalConnectClient

logging.basicConfig(filename="test.log", level=logging.DEBUG)

if len(sys.argv) < 2 or len(sys.argv) > 3:
    print("usage:  python3 -m total_connect_client username [password]\n")
    sys.exit(1)


USERNAME = sys.argv[1]
if len(sys.argv) == 2:
    PASSWORD = getpass.getpass()
else:
    PASSWORD = sys.argv[2]

TC = TotalConnectClient(USERNAME, PASSWORD)

for x in range(10000):
    print(f"request {x}")
    for location in TC.locations.values():
        location.get_panel_meta_data()
    sleep(30)

print(f"Function run times:\n{TC.times_as_string()}")

TC.log_out()
