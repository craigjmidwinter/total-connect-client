"""Test your system from the command line."""

import sys
import logging
from pprint import pprint
import TotalConnectClient

logging.basicConfig(filename='test.log', level=logging.DEBUG)

if len(sys.argv) != 3:
    print('usage:  python3 test.py username password \n')
    exit()


print('using username: ' + sys.argv[1])
print('using password: ' + sys.argv[2])

print('\n\n\n')

tc = TotalConnectClient.TotalConnectClient(sys.argv[1], sys.argv[2], auto_bypass_battery=True)
location_id = next(iter(tc.locations))

print('\n\n\n')

print('--- panel meta data ---')
meta_data = tc.get_panel_meta_data(location_id)
pprint(meta_data)

print('\n\n\n')

print(tc.locations[location_id])

for z in tc.locations[location_id].zones:
    print(tc.locations[location_id].zones[z])

result = tc.request('GetZonesListInStateEx_V1(self.token, ' + str(location_id) + ', {"int": ["1"]}, 0)')
print('Result Code: {}\n'.format(result['ResultCode']))
pprint(result)
