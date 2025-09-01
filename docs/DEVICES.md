# Device information

Information on devices found through testing.

Real Device | DeviceName | DeviceClassID | PanelType | PanelVariant | SecurityPanelTypeID | Notes
------------ | - | - | - | - | - | -
Lynx Touch 7000 | ILP5 | 1 | 8 | 0 | None |
Vista-21IP | Security Panel | 1 | 2 | 1 | None | #36
ProA7Plus | Security System | 1 | 12 | 1 | None | 
ProA7Plus Z-Wave | Automation  | 3 | None | None | None | #213
ProA7Plus camera | Built-In Camera  | 6 | None | None | None | #213
Skybell HD | WiFi DoorBell | 7 | not returned | not returned | None | 
MyQ Garage Door | Garage Door | 303 | None | None | None | #213

## Device calls
Device | GetAutomationDeviceStatus | GetAutomationDeviceStatusExV1 | GetAllAutomationDeviceStatusExV1 | GetSceneList | GetDeviceStatus | Notes
------------ | - | - | - | - | - | -
Device 6485747 (Security System) | -12104 |  -12104 | -12104 | 0 | 0 | 
Device 6485748 (Automation) | -12104 | -12104 | -12104 | 0 | 0 | 
Device 6485749 (Built-In Camera) | -4004 | -4004 | -4004 | 0 | 0 | 
Device 222896 (Front Lock) | -4002 | -4002 | -4002 | -4002 | 0 | 
Device 452185 (Garage Door) | -4002 | -4002 | -4002 | -4002 | 0 | 
Device 6485914 (FRONT DOOR) | -4004 | -4004 | -4004 | 0 | 0 | 
Skybell HD | -4004 | -4004 | -4004 | 0 | 0 | @austinmroczek
ProA7Plus Built-In Camera | -4004 | -4004 | -4004 | 0 | 0 | @austinmroczek
ProA7Plus | -12104 |  -12104 | -12104 | 0 | 0 | @austinmroczek

"GetDeviceStatus" always returns success but DeviceInfo = None

## Camera stuff

Device | GetAllRSIDeviceStatus | GetLocationAllCameraList | GetLocationAllCameraListEx | GetLocationCameraList | GetPartnerCameraStatus | GetVideoPIRLocationDeviceList
------------ | - | - | - | - | - | -
Skybell HD | No | WiFiDoorbellList | WifiDoorbellList | No | wifidoorbellinfo | No
ProA7Plus builtin | No | No | No | No | No | VideoPIRInfo

GetLocationCameraList doesn't return anything
GetLocationAllCameraList returns same as GetLocationAllCameraListEx