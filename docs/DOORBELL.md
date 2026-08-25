# Doorbell

**Mode:** Reference (empirical, thin). This page is intentionally sparse —
doorbell/camera support (Skybell HD via `TotalConnectLocation.get_cameras()`,
see [`api-reference.md`](api-reference.md)) is far less exercised than
arm/disarm/zone status, and most of what's known is recorded in
[`DEVICES.md`](DEVICES.md)'s "Camera stuff" section instead of here. The
`TBD` cells below are honestly TBD, not a formatting placeholder — nobody has
recorded what these calls return yet. If you have a Skybell HD and can
capture this, a PR filling in the table is welcome.

> **Unicorn cameras used to crash `get_cameras()`. Fixed.**
>
> `_get_unicorn()` guarded on `"UnicornList"` and then read
> `"UnicornsList"`, which is not a key the API returns, so `get_cameras()`
> raised `KeyError('UnicornsList')` for anyone owning a Unicorn camera. The
> real nesting is `UnicornList → UnicornList → UnicornInfo`, recovered from
> a response posted in
> [issue #216](https://github.com/craigjmidwinter/total-connect-client/issues/216)
> and now pinned by `RESPONSE_CAMERA_LIST_UNICORN` in `tests/const.py` —
> this project's first camera fixture.
>
> The doorbell path was checked against that same capture and is **correct**:
> the response carries `WiFiDoorbellList`, exactly as the code expects. The
> lowercase `WifiDoorbellList` in [`DEVICES.md`](DEVICES.md)'s "Camera stuff"
> table is a transcription slip in that doc.
>
> **Still wanted:** a `GetLocationAllCameraListEx` capture from a **Skybell
> HD**. The #216 response came from an account whose `WiFiDoorbellList` was
> `null`, so the doorbell branch has a verified key but no verified *payload*
> — the `TBD` cells below are still TBD. Send the JSON with location IDs,
> device IDs, serial numbers and tokens removed; the key names and structure
> are what matter, not the values. Scrub per
> [`../SECURITY.md`](../SECURITY.md) first — debug captures can contain
> credentials.

## Device calls

Device | GetWiFiDoorBellDeviceDetails | GetWiFiDoorBellDeviceDiagnosticDetails | GetWiFiDoorBellSettings | Notes
------------ | - | - | - | - 
Skybell HD | TBD | TBD | TBD | none

