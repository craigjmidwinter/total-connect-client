# Device information

**Mode:** Reference (empirical). Resideo's
[generated API reference](https://rs.alarmnet.com/TC2API.TCResource/) does not
include a complete device/panel catalogue. Every row below was recovered from
real accounts by contributors (see the `@austinmroczek` attributions and linked
issues) — this is the raw
data behind `total_connect_client.device.TotalConnectDevice.model_info()`'s
`MODEL_LOOKUP` table (see
[`api-reference.md`](api-reference.md#totalconnectdevice)). If your hardware
isn't listed here, `model_info()` returns `("Unknown model", "Unknown model
ID")` and logs a warning asking you to report it — please do; that's how this
table grows.

**How to read this page:** the first table maps observed
`(DeviceClassID, PanelType, PanelVariant)` combinations (from a device's
`DeviceFlags`) to real hardware; the second and third tables record which
device-status API calls succeed vs. fail (`ResultCode`, cross-reference
[`RESULT_CODES.md`](RESULT_CODES.md)) for each device kind.

**Worked example:**

```python
for device in location.devices.values():
    model, model_id = device.model_info()
    print(device.name, model, model_id)
    # "Security Panel" ProA7 Plus   (DeviceClassID=1, PanelType=12, PanelVariant=1 -> row below)
```

| Real Device      | DeviceName      | DeviceClassID | PanelType    | PanelVariant | SecurityPanelTypeID | Notes |
| ---------------- | --------------- | ------------- | ------------ | ------------ | ------------------- | ----- |
| Vista-21IP       | Security Panel  | 1             | 2            | 1            | None                | # 36  |
| Lynx Plus        | Security Panel  | 1             | 5            | 1            | None                | # 66  |
| Lynx Touch 7000  | ILP5            | 1             | 8            | 0            | None                |       |
| Lynx Touch 5210  | ILP5            | 1             | 8            | 1            | None                | # 85  |
| LCP500-L         | Security System | ?             | 10           | 1            | null                | # 163 |
| ProA7Plus        | Security System | 1             | 12           | 1            | 12                  |       |
| Vista            | LTEM-PV/PIV     | 1             | 15           | 1            | 15                  | # 264 |
| ProA7Plus Z-Wave | Automation      | 3             | None         | None         | None                | # 213 |
| ProA7Plus camera | Built-In Camera | 6             | None         | None         | None                | # 213 |
| Skybell HD       | WiFi DoorBell   | 7             | not returned | not returned | None                |       |
| MyQ Garage Door  | Garage Door     | 303           | None         | None         | None                | # 213 |

## Device calls

| Device                           | GetAutomationDeviceStatus | GetAutomationDeviceStatusExV1 | GetAllAutomationDeviceStatusExV1 | GetSceneList | GetDeviceStatus | Notes          |
| -------------------------------- | ------------------------- | ----------------------------- | -------------------------------- | ------------ | --------------- | -------------- |
| Device 6485747 (Security System) | -12104                    | -12104                        | -12104                           | 0            | 0               |
| Device 6485748 (Automation)      | -12104                    | -12104                        | -12104                           | 0            | 0               |
| Device 6485749 (Built-In Camera) | -4004                     | -4004                         | -4004                            | 0            | 0               |
| Device 222896 (Front Lock)       | -4002                     | -4002                         | -4002                            | -4002        | 0               |
| Device 452185 (Garage Door)      | -4002                     | -4002                         | -4002                            | -4002        | 0               |
| Device 6485914 (FRONT DOOR)      | -4004                     | -4004                         | -4004                            | 0            | 0               |
| Skybell HD                       | -4004                     | -4004                         | -4004                            | 0            | 0               | @austinmroczek |
| ProA7Plus Built-In Camera        | -4004                     | -4004                         | -4004                            | 0            | 0               | @austinmroczek |
| ProA7Plus                        | -12104                    | -12104                        | -12104                           | 0            | 0               | @austinmroczek |

"GetDeviceStatus" always returns success but DeviceInfo = None

## Camera stuff

| Device            | GetAllRSIDeviceStatus | GetLocationAllCameraList | GetLocationAllCameraListEx | GetLocationCameraList | GetPartnerCameraStatus | GetVideoPIRLocationDeviceList |
| ----------------- | --------------------- | ------------------------ | -------------------------- | --------------------- | ---------------------- | ----------------------------- |
| Skybell HD        | No                    | WiFiDoorbellList         | WifiDoorbellList           | No                    | wifidoorbellinfo       | No                            |
| ProA7Plus builtin | No                    | No                       | No                         | No                    | No                     | VideoPIRInfo                  |

GetLocationCameraList doesn't return anything
GetLocationAllCameraList returns same as GetLocationAllCameraListEx
