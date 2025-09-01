# Zone Types

## Zone Types returned by REST API

Request: https://rs.alarmnet.com/TC2API.TCResource/api/v1/SecuritySystem/ZoneTypes
Response: 
```json
{'ZoneTypeInfoList': {'ZonesTypeInfo': [{'ZoneTypeId': 0, 'ZoneTypeDescription': 'Assign for Unused Zones/Disabled ', 'CanBeBypassed': 1}, {'ZoneTypeId': 1, 'ZoneTypeDescription': 'Entry/Exit #1, Burglary ', 'CanBeBypassed': 1}, {'ZoneTypeId': 2, 'ZoneTypeDescription': 'Entry/Exit #2, Burglary ', 'CanBeBypassed': 1}, {'ZoneTypeId': 3, 'ZoneTypeDescription': 'Perimeter, Burglary ', 'CanBeBypassed': 1}, {'ZoneTypeId': 4, 'ZoneTypeDescription': 'Interior Follower, Burglary ', 'CanBeBypassed': 1}, {'ZoneTypeId': 5, 'ZoneTypeDescription': 'Trouble Day/Alarm Night ', 'CanBeBypassed': 1}, {'ZoneTypeId': 6, 'ZoneTypeDescription': '24 Hr. Silent Alarm ', 'CanBeBypassed': 1}, {'ZoneTypeId': 7, 'ZoneTypeDescription': '24 Hr. Audible Alarm ', 'CanBeBypassed': 1}, {'ZoneTypeId': 8, 'ZoneTypeDescription': '24 Hr. Auxiliary ', 'CanBeBypassed': 1}, {'ZoneTypeId': 9, 'ZoneTypeDescription': 'Fire Without Verification ', 'CanBeBypassed': 0}, {'ZoneTypeId': 10, 'ZoneTypeDescription': 'Interior Delay, Burglary ', 'CanBeBypassed': 1}, {'ZoneTypeId': 12, 'ZoneTypeDescription': 'Panel Link Supervision (C) 24 hour Monitor (R)', 'CanBeBypassed': 1}, {'ZoneTypeId': 13, 'ZoneTypeDescription': 'Remote P/S (*C) ', 'CanBeBypassed': 1}, {'ZoneTypeId': 14, 'ZoneTypeDescription': 'CO Detector Alarm (Carbon Monoxide) ', 'CanBeBypassed': 0}, {'ZoneTypeId': 15, 'ZoneTypeDescription': '24-hour Medical (*R) ', 'CanBeBypassed': 0}, {'ZoneTypeId': 16, 'ZoneTypeDescription': 'Fire With Verification', 'CanBeBypassed': 0}, {'ZoneTypeId': 17, 'ZoneTypeDescription': 'Fire Water flow (*C)', 'CanBeBypassed': 1}, {'ZoneTypeId': 18, 'ZoneTypeDescription': 'Fire Supervisory (*C)', 'CanBeBypassed': 1}, {'ZoneTypeId': 19, 'ZoneTypeDescription': '24-Hour Trouble (*C)', 'CanBeBypassed': 1}, {'ZoneTypeId': 20, 'ZoneTypeDescription': 'Arm–STAY(5800 Series devices only)', 'CanBeBypassed': 1}, {'ZoneTypeId': 21, 'ZoneTypeDescription': 'Arm AWAY(5800 Series devices only)', 'CanBeBypassed': 1}, {'ZoneTypeId': 22, 'ZoneTypeDescription': 'Disarm(5800 Series devices only)', 'CanBeBypassed': 1}, {'ZoneTypeId': 23, 'ZoneTypeDescription': 'No Alarm Response (e.g., relay activation)', 'CanBeBypassed': 1}, {'ZoneTypeId': 24, 'ZoneTypeDescription': 'Silent Burglary (*R)', 'CanBeBypassed': 1}, {'ZoneTypeId': 25, 'ZoneTypeDescription': '24-Hour Jiffy Lube (*R)', 'CanBeBypassed': 1}, {'ZoneTypeId': 27, 'ZoneTypeDescription': 'Access Point (*C)', 'CanBeBypassed': 1}, {'ZoneTypeId': 28, 'ZoneTypeDescription': 'Main Logic Board (MLB) Supervision- Not', 'CanBeBypassed': 1}, {'ZoneTypeId': 29, 'ZoneTypeDescription': 'Momentary Exit (used with VistaKey module)', 'CanBeBypassed': 1}, {'ZoneTypeId': 50, 'ZoneTypeDescription': 'Garage Door', 'CanBeBypassed': 1}, {'ZoneTypeId': 53, 'ZoneTypeDescription': 'Garage Monitor', 'CanBeBypassed': 1}, {'ZoneTypeId': 59, 'ZoneTypeDescription': 'Awareness', 'CanBeBypassed': 1}, {'ZoneTypeId': 77, 'ZoneTypeDescription': 'Keyswitch (*R)', 'CanBeBypassed': 1}, {'ZoneTypeId': 81, 'ZoneTypeDescription': 'AAV Monitor (*R)', 'CanBeBypassed': 1}, {'ZoneTypeId': 85, 'ZoneTypeDescription': 'Resi. Monitor', 'CanBeBypassed': 1}, {'ZoneTypeId': 86, 'ZoneTypeDescription': 'Resi. Response', 'CanBeBypassed': 1}, {'ZoneTypeId': 87, 'ZoneTypeDescription': 'No confirm Resi. Monitor', 'CanBeBypassed': 1}, {'ZoneTypeId': 88, 'ZoneTypeDescription': 'No confirm Resi. Response', 'CanBeBypassed': 1}, {'ZoneTypeId': 89, 'ZoneTypeDescription': 'Local Alarm', 'CanBeBypassed': 1}, {'ZoneTypeId': 90, 'ZoneTypeDescription': '??', 'CanBeBypassed': 1}, {'ZoneTypeId': 91, 'ZoneTypeDescription': '??', 'CanBeBypassed': 1}, {'ZoneTypeId': 92, 'ZoneTypeDescription': '??', 'CanBeBypassed': 1}, {'ZoneTypeId': 93, 'ZoneTypeDescription': '??', 'CanBeBypassed': 1}, {'ZoneTypeId': 94, 'ZoneTypeDescription': 'Awareness', 'CanBeBypassed': 1}, {'ZoneTypeId': 95, 'ZoneTypeDescription': '24-Hr. Awareness', 'CanBeBypassed': 1}, {'ZoneTypeId': 201, 'ZoneTypeDescription': 'SixRepeater', 'CanBeBypassed': 0}, {'ZoneTypeId': 205, 'ZoneTypeDescription': 'Tablet', 'CanBeBypassed': 1}, {'ZoneTypeId': 223, 'ZoneTypeDescription': 'Final Door', 'CanBeBypassed': 1}]}}
```

## Information on devices found through testing with SOAP 

Zone Type # | Type | Notes
------------ | - | -
0 | Security | Lynx Touch 7000 and sensors 5820L, 5818MNL, 5800RPS, 5898.  Lynx Touch 7000 with 5898 set as Temperature.
1 | Entry/Exit 1 | Lyric and 5800MINI
2 | Entry/Exit 2 |
3 | Perimeter | 5800mini via the ProA7Plus "takeover" module
4 | Interior Follower | Lyric and SiXPIR motion
5 | Trouble | Trouble by day, alarm by night
6 | Silent 24 Hour | 
7 | Audible 24 Hour | ProA7Plus police button
8 | Auxilliary 24 Hour | 
9 | Fire/Smoke | Lynx Touch 7000 and 5808W3 smoke detectors.  Lynx Touch 7000 Fire button.  Lynx Touch 7000 with 5898 set as Heat.
10 | Interior Delay | ProSixMini2 set to Interior with Delay via ProA7Plus panel
12 | Monitor | Lyric "Temperature", ProSixFlood via ProA7Plus panel
14 | Carbon Monoxide | Lynx Touch 7000 and 5800CO sensors
15 | Medical | ProA7Plus medical button
16 | Fire with verification | Must trigger twice to cause an alarm
20 | RF Arm Stay | Keyfob
21 | RF Arm Away | Keyfob
22 | RF Disarm | Keyfob
23 | No Alarm Response | Per Vista docs
24 | Silent Burglary | Per Vista docs
50 | Keypad | Lyric Keypad
53 | Garage Monitor | reported by ProA7 with SiX C2W
77 | Keyswitch | Per Vista20P docs
81 | AAV Monitor | Tells that audio session in progress
89 | tbd | Lyric "local alarm"
90-93 | Vista configurable | (not yet seen in the wild)

See 
- https://www.alarmliquidators.com/content/Vista%2021IP-%20Programming%20Guide.pdf
- http://techresource.online/training/ssnw/honeywell/zone-types
- http://www.honeywellmanual.com/pdf/vista20p.pdf

