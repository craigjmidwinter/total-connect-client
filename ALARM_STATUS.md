# Alarm Status information

The status codes from Total Connect are not well documented.  Here are some results that have been found through testing.

## ArmingState
ArmingState is reported per Partition.  Most systems will only have one partition with a PartitionID of '1'.

Code | Status
------------ | -------------
10200 | Disarmed
10201 | Armed Away
10202 | Armed Away bypass
10203 | Armed Stay
10204 | Armed Stay Bypass
10205 | Armed Away instant
10206 | Armed Away instant bypass
10207 | Alarming.  This code is reported for perimeter sensor devices (doors and windows).  It is also reported for manually pushed buttons on the panel Medical and Police. 
10209 | Armed Stay Instant
10210 | Armed Stay Instant Bypass
10211 | Disarmed bypass
10212 | Alarming Fire/Smoke. This code is reported for smoke detectors.  It is also reported for manually pushed buttons on the panel for Fire.
10213 | Alarming Carbon Monoxide
10218 | Armed Stay Night
10223 | Armed custom bypass
10307 | Arming
10308 | Disarming

## ZoneStatus
ZoneStatus is reported per Zone.

Code | Status
------------ | -------------
0 | Normal
1 | Bypassed
2 | Fault
8 | Tamper
72 | Trouble (low battery)
256 | Alarm/Triggered

Fault is only returned when "Sensor Events" are enabled for a specific zone in Total Connect, otherwise Normal is returned.
