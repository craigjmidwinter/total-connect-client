import TotalConnectClient
import sys
from pprint import pprint

if len(sys.argv) != 3:
  print('usage:  python3 test.py username password \n')
else:

  print('using username: ' + sys.argv[1] + '\n')
  print('using password: ' + sys.argv[2] + '\n')

  print('\n\n\n')

#  print('--- all location/system data ---')
  tc = TotalConnectClient.TotalConnectClient(sys.argv[1], sys.argv[2])
  location = tc.get_location_by_location_name()
#  pprint(location)

  print('\n\n\n')

  print('--- Devices name(s) ---')
  for device in location['DeviceList']['DeviceInfoBasic']:
    print(device['DeviceName'])
