"""Test your system from the command line."""

import logging
import sys
from pprint import pprint

from total_connect_client.client import TotalConnectClient

logging.basicConfig(filename="test.log", level=logging.DEBUG)

if len(sys.argv) != 7:
    print(
        "usage:  username password AutomationDeviceID DeviceID DeviceTypeID LocationID\n"
    )
    sys.exit()

USERNAME = sys.argv[1]
PASSWORD = sys.argv[2]
AUTOMATION_DEVICE = sys.argv[3]
DEVICE_ID = sys.argv[4]
TYPE = sys.argv[5]
LOCATION = sys.argv[6]

TC = TotalConnectClient(USERNAME, PASSWORD)

print("\n\n\nGetAutomationDeviceStatus\n\n\n")
result = TC.request(f"GetAutomationDeviceStatus(self.token, {AUTOMATION_DEVICE})")

pprint(result)


print("\n\n\nGetAutomationDeviceStatusExV1\n\n\n")
result = TC.request(f"GetAutomationDeviceStatusExV1(self.token, {AUTOMATION_DEVICE})")

pprint(result)


print("\n\n\nGetAllAutomationDeviceStatusExV1\n\n\n")
result = TC.request(
    f"GetAllAutomationDeviceStatusExV1(self.token, {AUTOMATION_DEVICE})"
)

pprint(result)


print("\n\n\nGetDeviceStatus\n\n\n")

a = []
a.append(DEVICE_ID)
a.append(TYPE)
b = []
b.append(a)

result = TC.request(f"GetDeviceStatus(self.token, {LOCATION}, {b})")


print("\n\n\nGetAutomationLocks\n\n\n")
result = TC.request(f"GetAutomationLocks(self.token, {AUTOMATION_DEVICE}, {DEVICE_ID})")

pprint(result)
