"""Test your system from the command line."""

import logging
import sys

import TotalConnectClient

logging.basicConfig(filename="test.log", level=logging.DEBUG)

if len(sys.argv) != 4:
    print("usage:  python3 test.py username password usercode \n")
    print("usercode = -1 is a good default")
    sys.exit()

tc = TotalConnectClient.TotalConnectClient(
    username=sys.argv[1], password=sys.argv[2], usercode=sys.argv[3]
)

print(tc)
