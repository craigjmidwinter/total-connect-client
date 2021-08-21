# Total-Connect-Client
Total-Connect-Client is a python client for interacting with the TotalConnect2 alarm system.

Started by @craigjmidwinter to add alarm support for his personal HomeAssistant set-up, with later contributions from others.

The package can be downloaded at [PyPI](https://pypi.org/project/total-connect-client/).

The code currently supports:
 - Arming (away, stay, night)
 - Disarming
 - Getting panel status (armed, bypassed, etc)
 - Getting zone status (normal, fault, trouble, low battery, etc)

## Troubleshooting

If you're having trouble with your system, or find an error message, we may ask you to submit information about your alarm system.  To do that from the command line do the following steps (assuming you are running from within Home Assistant):
 
`python3 -m total_connect_client.info username password`
 
If you want to easily put the info into a file for sharing: 
 - `python3 -m total_connect_client.info username password > my_info.txt`
 - Now the file my_info.txt in the same directory will hold all of that information

**WARNING**:  the output of this command includes private information including your username and password.  Carefully remove it before sharing with the developers or posting on Github.

Create an Issue on Github and post both your problem and your system information.

Why do we ask for this information?  The TotalConnect API documentation provides little information on the status codes and other information it returns about your system.  We developed as best we could using the codes our own systems returned.  We have seen many times that other users with issues have different system status codes.

## Developer Interface

If you're an end user, just install Home Assistant and things should just work.

If you're a developer and want to interface to TotalConnect from a system other than Home Assistant:

```
pip install total-connect-client
```

```
from total_connect_client import TotalConnectClient, ArmType, ArmingHelper
```

To arm or disarm the system you must provide the usercode.
The usercodes dictionary maps locationid to usercode; if
the locationid is not found it uses the default usercode.
```python
usercodes = { 'default': '1234' }
client = TotalConnectClient(username, password, usercodes)

for location in client.locations:
    # location.arming_state can be matched against the ArmingState enum members
    # or you can call the ArmingState convenience methods:
    location.arming_state.is_disarmed()
    location.arming_state.is_armed() # true if system is armed in any way
    location.arming_state.is_armed_away()
    location.arming_state.is_pending() # true if system is arming or disarming
    location.arming_state.is_triggered() # true if system is in any alarm state
    location.arming_state.is_triggered_gas() # true if in carbon monoxide alarm state
    #    and many more convenience methods

    # you can pass one of the ArmType enum members to location.arm(), e.g.
    #    location.arm(ArmType.STAY_INSTANT)
    # or, equivalently, you can use any of the specific methods on ArmingHelper:
    #    ArmingHelper(location).arm_away()

    location.disarm()

    location.zone_bypass(zoneid)

    location.is_ac_loss()
    location.is_low_battery()
    location.is_cover_tampered()
    location.last_updated_timestamp_ticks
    location.configuration_sequence_number

    for (zone_id, zone) in location.zones.items():
        zone.is_bypassed()
        zone.is_faulted()
        zone.is_tampered()
        zone.is_low_battery()
        zone.is_troubled()
        zone.is_triggered()

        # zone.zone_type_id can be matched against the ZoneType enum members,
        # or you can call the following convenience methods:
        zone.is_type_button()
        zone.is_type_security()
        zone.is_type_motion()
        zone.is_type_fire() # heat detector or smoke detector
        zone.is_type_carbon_monoxide()
        zone.is_type_medical()

        zone.partition # the partition ID
        zone.description
        zone.can_be_bypassed
        zone.status
        zone.battery_level
        zone.signal_strength
        zone.chime_state
        zone.supervision_type
        zone.alarm_report_state
        zone.loop_number
        zone.sensor_serial_number
        zone.device_type

    # to refresh a location
    location.get_partition_details()
    location.get_zone_details()
    location.get_panel_meta_data()

    # to arm or disarm by partition
    for (partition_id, partition) in location.partitions.items():
        ArmingHelper(partition).arm_stay()
        etc.
```

## Recent Interface Changes

* Partition support has been added. The TotalConnectLocation.arm and disarm family of methods now accept an optional partition_id parameter, and a single TotalConnectPartition object has arm() and disarm() methods and can be used with ArmingHelper.
* Previously most methods returned True on success and False on failure, with no exceptions expected. Now successful methods return but on failure raise subclasses of TotalConnectError.
* The arming control methods in TotalConnectClient have been deprecated; instead use the
similar methods on the values of self.locations.

## Likely Future Interface Changes

* Previously if the usercodes dictionary was invalid, the DEFAULT_USERCODE
was silently used. In a future release, we will raise an exception on an invalid dictionary.

If there's something about the interface you don't understand, check out the (Home Assistant integration)[https://github.com/home-assistant/core/blob/dev/homeassistant/components/totalconnect/] that uses this package, or submit an issue here.

During development, if you discover new status codes or other information not handled, please submit an issue to let us know, or even better submit a pull request.
