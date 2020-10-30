"""Test your system from the command line."""

import logging
import sys

import TotalConnectClient

logging.basicConfig(filename="test.log", level=logging.DEBUG)

if len(sys.argv) != 3:
    print("usage:  python3 test.py username password\n")
    sys.exit()


USERNAME = sys.argv[1]
PASSWORD = sys.argv[2]

TC = TotalConnectClient.TotalConnectClient(USERNAME, PASSWORD)

print(TC)
