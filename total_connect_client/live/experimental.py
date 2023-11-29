"""Experimental API calls to find new capability."""

import logging
import sys
import getpass
from pprint import pprint

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


def request_location(request_name, location_id):
    """Request with just location and token."""
    print(f"\n\n{request_name}: {location_id}")
    try:
        result = TC.request(request_name, (TC.token, location_id))
        pprint(result)
    except Exception as err:
        print(err)


def request_device(request_name, device_id):
    """Request with just device and token."""
    print(f"\n\n{request_name}: {device_id}")
    try:
        result = TC.request(request_name, (TC.token, device_id))
        pprint(result)
    except Exception as err:
        print(err)


print("GetDoorBellClientID")
try:
    result = TC.request("GetDoorBellClientID", (TC.token,))
    pprint(result)
except Exception as err:
    print(err)

for location_id, location in TC.locations.items():
    print(f"{location}")

    # camera
    request_location("GetAllRSIDeviceStatus", location_id)
    request_location("GetLocationAllCameraList", location_id)
    request_location("GetLocationAllCameraListEx", location_id)
    request_location("GetLocationCameraList", location_id)
    request_location("GetPartnerCameraStatus", location_id)
    request_location("GetVideoPIRLocationDeviceList", location_id)

    # doorbell
    request_location("GetWiFiDoorBellDeviceDetails", location_id)
    request_location("GetWiFiDoorBellDeviceDiagnosticDetails", location_id)
    request_location("GetWiFiDoorBellSettings", location_id)

    # thermostat
    request_location("GetWiFiThermostatLocations", location_id)

    # lock
    request_location("GetWiFiLockLocations", location_id)

    # automation / scenes
    request_location("GetSmartActionConfiguration", location_id)
    request_location("GetSmartSceneConfiguration", location_id)
    request_location("GetSmartSceneList", location_id)

    print(f"\n\nGetSmartActionList: {location_id} with no array")
    try:
        result = TC.request("GetSmartActionList", (TC.token, location_id, None, True))
        pprint(result)
    except Exception as err:
        print(err)
    print(f"\n\nGetSmartActionList: {location_id} with empty array")
    try:
        result = TC.request("GetSmartActionList", (TC.token, location_id, [], True))
        pprint(result)
    except Exception as err:
        print(err)

    for device_id, device in location.devices.items():
        print(f"{device}")

        request_device("GetAutomationDeviceStatus", device_id)
        request_device("GetAutomationDeviceStatusExV1", device_id)
        request_device("GetAllAutomationDeviceStatusExV1", device_id)
        request_device("GetSceneList", device_id)
        request_device("GetDeviceStatus", device_id)
