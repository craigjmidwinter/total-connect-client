"""Test your system from the command line."""

import getpass
import logging
import sys

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

print(TC)
