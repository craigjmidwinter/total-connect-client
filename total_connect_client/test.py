import TotalConnectClient
import sys
from pprint import pprint

import logging
logging.basicConfig(filename='test.log',level=logging.DEBUG)

if len(sys.argv) != 3:
  print('usage:  python3 test.py username password \n')
else:

  print('using username: ' + sys.argv[1] + '\n')
  print('using password: ' + sys.argv[2] + '\n')

  print('\n\n\n')

  print('--- all location/system data ---')
  tc = TotalConnectClient.TotalConnectClient(sys.argv[1], sys.argv[2])
  location = tc.get_location_by_location_name()
  pprint(location)

  print('\n\n\n')

  print('--- panel meta data ---')
  meta_data = tc.get_panel_meta_data()
  pprint(meta_data)

  print('\n\n\n')

  print('--- Devices name(s) ---')
  for device in location['DeviceList']['DeviceInfoBasic']:
    print(device['DeviceName'])

  print('--- Device Status ---')
  print('Low Battery: ' + str(tc.low_battery))
  print('AC Loss: ' + str(tc.ac_loss))
