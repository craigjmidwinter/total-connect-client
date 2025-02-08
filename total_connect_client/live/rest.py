"""Test REST API from the command line."""

import getpass
import logging
import sys
import time

from total_connect_client.client import TotalConnectClient
from total_connect_client.const import ArmType
from total_connect_client.exceptions import TotalConnectError

logging.basicConfig(filename="test.log", level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)

if len(sys.argv) != 3:
    print("usage:  username location1=usercode1,location2=usercode2 \n")
    sys.exit()

USERNAME = sys.argv[1]
USERCODES = dict(x.split("=") for x in sys.argv[2].split(","))
PASSWORD = getpass.getpass()

print("Starting test script")
LOGGER.debug("Starting test script")
TC = TotalConnectClient(USERNAME, PASSWORD, USERCODES)

print("Data from client startup\n\n")
print(TC)

print("Attempt to sync.")
LOGGER.debug("Attempt to sync")
for location_id in TC.locations:
    try:
        TC.locations[location_id].sync_panel()
    except TotalConnectError as error:
        LOGGER.error(error)
        print(error)

print("Attempt to validate usercodes.")
LOGGER.debug("Attempt validate usercodes")
for location_id in USERCODES:
    result = TC.locations[int(location_id)].validate_usercode(USERCODES[location_id])
    print(
        f"Usercode {USERCODES[location_id]} valid at location {location_id}: {result}"
    )

print("Attempt zone bypass all.")
LOGGER.debug("Attempt zone bypass all")
for location_id in TC.locations:
    try:
        TC.locations[location_id].zone_bypass_all()
    except TotalConnectError as error:
        LOGGER.error(error)
        print(error)
"""
print("Attempt to arm stay.")
LOGGER.debug("Attempt arm stay")
for location_id in TC.locations:
    try:
        TC.locations[location_id].arm(ArmType.STAY)
    except TotalConnectError as error:
        LOGGER.error(error)
        print(error)
"""
for location_id in TC.locations:
    try:
        TC.locations[location_id].get_panel_meta_data()
    except TotalConnectError as error:
        LOGGER.error(error)
        print(error)

print("Sleep 5 seconds....")
time.sleep(5)
print("Attempt to disarm.")
LOGGER.debug("Attempt disarm")
for location_id in TC.locations:
    try:
        TC.locations[location_id].disarm()
    except TotalConnectError as error:
        LOGGER.error(error)
        print(error)


print("Attempt to clear bypass.")
LOGGER.debug("Attempt clear bypass")
for location_id in TC.locations:
    try:
        TC.locations[location_id].clear_bypass()
    except TotalConnectError as error:
        LOGGER.error(error)
        print(error)

print(TC.times_as_string())

LOGGER.debug("Attempt to log out")
TC.log_out()


sys.exit()
