# API reference

**Mode:** Reference. Every signature below is copied from the source
(`total_connect_client/*.py`) as of release `2026.7`; if you're reading this
against a different version, check the signature in the installed package —
this is a library whose entire value is its API surface, so accuracy here
matters more than prose. Where the code's actual behavior is surprising, that
is called out explicitly rather than smoothed over.

For *why* the client is shaped this way (the auth flow, the retry model), see
[`architecture.md`](architecture.md). For a narrative walkthrough, see
[`DEVELOPER.md`](DEVELOPER.md).

## Minimal working example

```python
from total_connect_client import ArmingHelper, ArmType, TotalConnectClient
from total_connect_client.exceptions import (
    AuthenticationError,
    ServiceUnavailable,
    TotalConnectError,
)

usercodes = {"default": "1234"}  # alarm usercode, not your TC2 account password

try:
    client = TotalConnectClient("me@example.com", "hunter2", usercodes)
except AuthenticationError:
    raise SystemExit("bad TotalConnect username/password")
except ServiceUnavailable:
    raise SystemExit("TotalConnect service unreachable; try again later")

for location in client.locations.values():
    print(location.location_name, location.arming_state)
    if location.arming_state.is_disarmed():
        try:
            ArmingHelper(location).arm_away()
        except TotalConnectError as err:
            print(f"could not arm {location.location_name}: {err}")
```

Note `client.locations.values()` — `client.locations` is
`dict[int, TotalConnectLocation]` keyed by location ID, not a list. Iterating
`client.locations` directly gives you the integer keys, not location objects.

---

## `TotalConnectClient`

`from total_connect_client import TotalConnectClient`

The entry point. Constructing one logs in immediately (see
[`architecture.md`](architecture.md) for the auth flow) and, by default, loads
every location's partitions, zones, and panel status before the constructor
returns.

### `TotalConnectClient(username, password, usercodes=None, auto_bypass_battery=False, retry_delay=6, load_details=True)`

```python
def __init__(
    self,
    username: str,
    password: str,
    usercodes: dict[str, str] | None = None,
    auto_bypass_battery: bool = False,
    retry_delay: int = 6,
    load_details: bool = True,
) -> None
```

| Parameter | Type | Default | Required | Description |
|---|---|---|---|---|
| `username` | `str` | — | yes | Your TotalConnect 2 account username (usually an email address). |
| `password` | `str` | — | yes | Your TotalConnect 2 account password. **Not** the alarm keypad usercode. |
| `usercodes` | `dict[str, str] \| None` | `None` | no | Maps a location to the alarm usercode used to arm/disarm/bypass at that location. See "The `usercodes` dict" below — the shape is more particular than the type hint suggests. |
| `auto_bypass_battery` | `bool` | `False` | no | If `True`, any zone reporting low battery that `can_be_bypassed` is automatically bypassed as zone data is refreshed (see `TotalConnectLocation._update_zones`). |
| `retry_delay` | `int` | `6` | no | Seconds to sleep between retry attempts on a retryable failure (see [Retries](#retries-and-reauthentication)). Tests set this to `0` to run fast. |
| `load_details` | `bool` | `True` | no | If `True`, the constructor calls `load_details()` before returning, fetching partitions/zones/panel status for every location. If `False`, `client.locations` is populated but each location has empty `partitions`/`zones` until you call `get_partition_details()` / `get_zone_details()` / `get_panel_meta_data()` yourself. |

**Returns:** nothing (constructs the client; raises on failure — see below).

**Raises:**
- `AuthenticationError` — bad username/password, or account locked.
- `ServiceUnavailable` — the TotalConnect config/token/session endpoints
  didn't respond successfully after retries.
- `TotalConnectError` — the account has zero locations (`"no locations
  found"`), or another unexpected condition during login.

```python
client = TotalConnectClient("me@example.com", "hunter2", {"default": "1234"})
```

#### The `usercodes` dict — sharp edges

The type hint says `dict[str, str]`, but the actual lookup
(`TotalConnectClient._make_locations`) is more permissive and more particular
than that hint implies:

```python
usercode = (
    self.usercodes.get(location_id)        # tried as an int key first
    or self.usercodes.get(str(location_id))  # then as a str key
    or self.usercodes.get("default")         # then the 'default' fallback
)
```

- `location_id` here is always an `int` (it comes straight off the parsed
  JSON `LocationID` field). The lookup tries the **int** key first, so
  `{123456: "1234"}` works even though the declared type is `dict[str, str]`.
  A `str(location_id)` key (`{"123456": "1234"}`) also works. Mixing styles in
  one dict is fine — each location is looked up independently.
- `"default"` is used if neither the int nor the str key for that specific
  location holds a **truthy** value. Note that is truthiness, not presence:
  the lookup is an `or` chain, so a key that *is* present but empty falls
  through. `{123456: "", "default": "9999"}` gives location `123456` the
  code `"9999"`, and `{123456: None, ...}` behaves the same. If you build
  this dict programmatically — say `{loc: cfg.get(loc, "") for loc in ...}`
  alongside a `"default"` entry — every location you meant to leave uncoded
  silently receives the default instead.
- **If none of the three match, the usercode is *not* an error.** The location
  silently gets `location.usercode = "-1"` (the `DEFAULT_USERCODE` sentinel
  string), and only a `LOGGER.debug` line notes it. Any subsequent
  `arm()`/`disarm()`/bypass call for that location will send usercode `-1` to
  the panel and get back a `USER_CODE_INVALID` or `USER_CODE_UNAVAILABLE`
  result, which surfaces as `UsercodeInvalid`/`UsercodeUnavailable` (see
  [Exceptions](#exceptions)) — not as a clear "you forgot a usercode for this
  location" error at construction time. This is a surprising failure mode: if
  you support multiple locations, make sure every location ID is covered by
  your `usercodes` dict or a `"default"` entry, because the client will not
  tell you it's missing until you try to arm/disarm/bypass.

```python
# one code for every location
usercodes = {"default": "1234"}

# per-location codes, falling back to default
usercodes = {123456: "1234", 654321: "5678", "default": "0000"}
```

### `client.locations`

```python
@property
def locations(self) -> dict[int, TotalConnectLocation]
```

Read-only. Maps `location_id` (`int`) → `TotalConnectLocation`. Populated
during construction (from the session-details response); never empty after a
successful construction (an account with zero locations raises
`TotalConnectError` during `__init__`, see above).

```python
for location_id, location in client.locations.items():
    print(location_id, location.location_name)
```

### Other `TotalConnectClient` methods

| Method | Signature | Returns | Raises | Notes |
|---|---|---|---|---|
| `is_logged_in` | `() -> bool` | Whether the client currently believes it holds a valid session. | — | Does not make a network call. |
| `log_out` | `() -> None` | `None` | `TotalConnectError` if the server reports logout failed | No-op if already logged out. |
| `get_number_locations` | `() -> int` | `len(self.locations)` | — | Exists because Home Assistant needs the count via a callable. |
| `load_details` | `(retries: int = 5) -> None` | `None` | — (swallows per-location exceptions internally and retries; logs `warning` if it still fails after `retries` attempts) | Called automatically by `__init__` unless `load_details=False`. |
| `raise_for_resultcode` | `(response: dict) -> None` | `None` on success | see [Exceptions](#exceptions) | You will not normally call this yourself — location/partition/zone methods call it after every request. Documented here because it is the single place that decides which exception a `ResultCode` becomes. |
| `http_request` | `(endpoint: str, method: str, params=None, data=None) -> dict` | Parsed JSON response body | `TotalConnectError`, `InvalidSessionError`, `RetryableTotalConnectError`, `ServiceUnavailable` | Low-level; used internally by every location/partition/zone call. You'd only call this directly to hit an endpoint this library doesn't wrap yet. |
| `times_as_string` | `() -> str` | A human-readable breakdown of time spent in named phases (`authenticate`, `__init__`, etc.) | — | Debugging aid, not for machine parsing. |

```python
client.log_out()
print(client.times_as_string())
```

---

## `TotalConnectLocation`

`from total_connect_client.location import TotalConnectLocation` — but you
never construct one yourself; you get instances from `client.locations`.

### Attributes

| Attribute | Type | Description |
|---|---|---|
| `location_id` | `int` | Stable identifier for this location. |
| `location_name` | `str` | Display name, as set in the TotalConnect account. |
| `security_device_id` | `str` | Identifier of the security panel device at this location; used to build arm/disarm/bypass endpoint URLs. |
| `ac_loss` | `bool \| None` | `True` if the panel reports AC power loss. `None` until first `get_panel_meta_data()`. |
| `low_battery` | `bool \| None` | `True` if the panel reports low battery. |
| `cover_tampered` | `bool \| None` | `True` if the panel cover is tampered. |
| `last_updated_timestamp_ticks` | `int \| None` | Panel-reported update timestamp (raw ticks, not a Unix timestamp). |
| `configuration_sequence_number` | `int \| None` | Opaque sequence number from the panel; changes when the panel config changes. |
| `arming_state` | `ArmingState` | Current arming state for the location as a whole. Starts as `ArmingState.UNKNOWN` until `get_panel_meta_data()` runs. |
| `partitions` | `dict[int, TotalConnectPartition]` | Keyed by partition ID. Empty until `get_partition_details()` runs. |
| `zones` | `dict[int, TotalConnectZone]` | Keyed by zone ID. Empty until `get_zone_details()` or `get_panel_meta_data()` runs. |
| `devices` | `dict[str, TotalConnectDevice]` | Keyed by device ID, populated at construction from the location's device list. |
| `usercode` | `str` | The usercode this location will use for arm/disarm/bypass calls when no per-call `usercode` argument is given. Set from the client's `usercodes` dict (see above) or defaulted to the `"-1"` sentinel. |
| `auto_bypass_low_battery` | `bool` | Copied from the client's `auto_bypass_battery` constructor argument — **a one-time copy, not a live link.** `_make_locations()` reads the client's value once while building locations, and that runs only from `TotalConnectClient.__init__`. Setting `client.auto_bypass_low_battery` afterwards changes nothing, silently: the bypass check reads *this* attribute, on the location. To change it on a live client, set it per location (`location.auto_bypass_low_battery = True`), which does work. |

### Methods that fetch/refresh state

| Method | Signature | Returns | Raises |
|---|---|---|---|
| `get_panel_meta_data` | `() -> None` | Updates `arming_state`, `ac_loss`, `low_battery`, `cover_tampered`, `last_updated_timestamp_ticks`, `configuration_sequence_number`, and every partition's/zone's status, in place. | `PartialResponseError` if the response is missing `PanelStatus` or `ArmingState`; `TotalConnectError` if `ArmingState` has a value not in the `ArmingState` enum; any exception `raise_for_resultcode` can raise (see [Exceptions](#exceptions)). |
| `get_zone_details` | `() -> None` | Populates `zones` with full per-zone metadata (battery, signal, serial number, etc.) beyond what `get_panel_meta_data` provides. | Catches `FeatureNotSupportedError` internally and only logs a warning — some accounts/hardware don't support this call, and that is not treated as fatal. Other `raise_for_resultcode` exceptions propagate. |
| `get_partition_details` | `() -> None` | Populates `partitions`. | `PartialResponseError` if the response has no `Partitions` section; `TotalConnectError` (re-raised after logging) on any other `raise_for_resultcode` failure. |

```python
location.get_partition_details()
location.get_zone_details()
location.get_panel_meta_data()
print(location.arming_state, len(location.zones), len(location.partitions))
```

### Arming and disarming

```python
def arm(self, arm_type: ArmType, partition_id: int = 0, usercode: str = "") -> None
def disarm(self, partition_id: int = 0, usercode: str = "") -> None
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `arm_type` (arm only) | `ArmType` | — required | One of the `ArmType` enum members (see below). |
| `partition_id` | `int` | `0` | `0` means "every partition at this location". A nonzero value arms/disarms only that partition; raises `TotalConnectError` if that partition ID doesn't exist at this location. |
| `usercode` | `str` | `""` | Overrides `self.usercode` for this call only. Empty string means "use the location's stored usercode". |

**Returns:** `None` on success.

**Raises:** `TotalConnectError` for an unknown `partition_id`; otherwise
whatever `raise_for_resultcode` raises for the arm/disarm response (commonly
`UsercodeInvalid`, `UsercodeUnavailable`, or `BadResultCodeError` if the panel
refuses — e.g. a faulted zone blocking arming, which the panel reports as
`COMMAND_FAILED` and this library logs a warning for before still raising).
`disarm()` is a no-op (returns immediately, no request sent) if the
target is already disarmed or already disarming.

```python
from total_connect_client import ArmType

location.arm(ArmType.STAY_INSTANT)      # arm every partition, Stay-Instant
location.arm(ArmType.AWAY, partition_id=1)  # arm only partition 1, Away
location.disarm()                        # disarm every partition
```

Equivalent, friendlier spelling via `ArmingHelper` — see below.

### Zone bypass

| Method | Signature | Returns | Raises | Notes |
|---|---|---|---|---|
| `zone_bypass` | `(zone_id: int) -> None` | `None` | `FailedToBypassZone`, or whatever else `raise_for_resultcode` raises | Bypasses one zone. |
| `zone_bypass_all` | `() -> None` | `None` | same | Bypasses every currently-faulted zone that `can_be_bypassed`. Zones that are faulted but not bypassable are logged and skipped, not raised. |
| `clear_bypass` | `() -> None` | `None` | whatever `raise_for_resultcode` raises | Clears every currently-bypassed zone. No-op if none are bypassed. |
| `zone_status` | `(zone_id: int) -> ZoneStatus` | The zone's cached `ZoneStatus` flags | `TotalConnectError` if `zone_id` isn't in `self.zones` | Reads cached state; does not hit the network. |

```python
location.zone_bypass(12)
location.zone_bypass_all()
location.clear_bypass()
```

**Sharp edge (as of the code's own comment, dated 12/31/2025):** a
successful bypass response comes back with `ResultCode` 0 (success) but the
returned `ZoneStatus` in that same response is still `0` (normal), not `1`
(bypassed). The zone's in-memory status is *not* updated by a successful
`zone_bypass()`/`zone_bypass_all()` call — only the next `get_panel_meta_data()`
or `get_zone_details()` call will show the zone as bypassed. Don't assert
`zone.is_bypassed()` immediately after calling `zone_bypass()`; refresh first.
Separately, `zone_bypass_all` returns SUCCESS even if a zone was already
bypassed before the call (see `RESULT_CODES.md`).

### Predicates

| Method | Returns |
|---|---|
| `is_ac_loss()` | `self.ac_loss is True` |
| `is_low_battery()` | `self.low_battery is True` |
| `is_cover_tampered()` | `self.cover_tampered is True` |

```python
if location.is_ac_loss():
    print(f"{location.location_name} lost AC power")
```

### Usercode management

| Method | Signature | Returns | Raises | Notes |
|---|---|---|---|---|
| `set_usercode` | `(usercode: str) -> bool` | `True` if the usercode validated and was set; `False` if validation failed | (validation errors are caught internally, not raised) | Sets `self.usercode` for *this client session only* — does not write anything to the panel. |
| `validate_usercode` | `(usercode: str) -> bool` | Whether the panel reports the usercode as a duplicate/in-use entry (`IsDuplicate`) | whatever `raise_for_resultcode` raises | Makes a network call. |

### Other location methods

`sync_panel()`, `get_cameras()`, and `trigger()` (explicitly marked
**experimental** in its docstring — it fires `RemotePanicAlarm`) are
documented in source but not detailed further here; read
`total_connect_client/location.py` directly before using `trigger()` against a
real panel. `arm_custom()` and `get_custom_arm_settings()` both unconditionally
raise `TotalConnectError("... is not operational yet")` — they exist as
placeholders, not working functionality.

---

## `TotalConnectPartition`

`from total_connect_client.partition import TotalConnectPartition` — you get
instances from `location.partitions`, never construct one yourself.

| Attribute | Type | Description |
|---|---|---|
| `partitionid` | `int` | Partition identifier, unique within its location. |
| `name` | `str \| None` | Partition name, if the panel provides one. |
| `is_stay_armed` | `bool \| None` | Whether this partition supports/uses stay-arming. |
| `is_fire_enabled` | `bool \| None` | Whether fire monitoring is enabled on this partition. |
| `is_common_enabled` | `bool \| None` | Whether this is a "common" partition (shared areas). |
| `is_locked` | `bool \| None` | Panel-reported lock state for the partition. |
| `is_new_partition` | `bool \| None` | Panel-reported "new partition" flag. |
| `is_night_stay_enabled` | `bool \| None` | Whether Stay-Night arming is available for this partition. |
| `exit_delay_timer` | `int \| None` | Exit delay, in seconds, as reported by the panel. |
| `arming_state` | `ArmingState` | This partition's own arming state (independent of the location's aggregate `arming_state`). |

```python
def arm(self, arm_type: ArmType, usercode: str = "") -> None
def disarm(self, usercode: str = "") -> None
```

Both are thin wrappers: `partition.arm(t, code)` calls
`partition.parent.arm(t, partition.partitionid, code)` (i.e. the
location's `arm()`/`disarm()` scoped to this partition). Same return/raise
behavior as `TotalConnectLocation.arm`/`disarm` above.

```python
for partition_id, partition in location.partitions.items():
    if partition.arming_state.is_disarmed():
        partition.arm(ArmType.STAY)
```

---

## `TotalConnectZone`

`from total_connect_client.zone import TotalConnectZone` (or import
`ZoneStatus`/`ZoneType` directly, see below) — instances come from
`location.zones`, never construct one yourself.

| Attribute | Type | Description |
|---|---|---|
| `zoneid` | `int` | Zone identifier, unique within its location. |
| `partition` | `int` | The partition ID this zone belongs to (`0` if unknown/unset). |
| `status` | `ZoneStatus` | Bit-flag status (see below). |
| `zone_type_id` | `ZoneType \| int \| None` | A `ZoneType` enum member if the raw ID is one this library recognizes, otherwise the raw `int` (unrecognized values are logged once and passed through — they are not fatal). See `ZONE_TYPES.md` for known raw values beyond the enum. |
| `can_be_bypassed` | `bool \| None` | Whether the panel allows bypassing this zone. |
| `description` | `str \| None` | Zone description/name as set in the panel. |
| `battery_level` | `int \| None` | Raw battery level as reported (units are panel-defined). |
| `signal_strength` | `int \| None` | Raw signal strength as reported. |
| `sensor_serial_number` | `str \| None` | Sensor's serial number, if reported. |
| `loop_number` | `int \| None` | Sensor loop number. |
| `response_type` | `str \| None` | Raw response type field. |
| `alarm_report_state` | `str \| None` | Raw alarm report state field. |
| `supervision_type` | `str \| None` | Raw supervision type field. |
| `chime_state` | `int \| None` | Raw chime state field. |
| `device_type` | `int \| None` | Raw device type field. |

### `ZoneStatus` (`IntFlag`)

```python
from total_connect_client import ZoneStatus
```

| Member | Value | Meaning |
|---|---|---|
| `NORMAL` | 0 | No flags set. |
| `BYPASSED` | 1 | Zone is bypassed. |
| `FAULT` | 2 | Zone is faulted/open — only populated if "Sensor Activities" is enabled on the account (see `README.md`). |
| `TROUBLE` | 8 | Zone reports trouble (also implies tamper, per source comment). |
| `TAMPER` | 16 | Zone tamper (ProA7-specific; see issue #176). |
| `COMMUNICATION_FAILURE` | 32 | Sensor communication failure (see issue #191). |
| `LOW_BATTERY` | 64 | Zone battery low. |
| `TRIGGERED` | 256 | Zone triggered/in alarm. |
| `KNOWN` | (bitwise OR of all of the above) | Used internally to detect and log unrecognized bits; not something you'd match against directly. |

Because this is an `IntFlag`, multiple bits can be set at once — check with
`&`, which is exactly what the predicate methods below do.

### Zone predicates

```python
def is_bypassed(self) -> bool     # status & ZoneStatus.BYPASSED > 0
def is_faulted(self) -> bool      # status & ZoneStatus.FAULT > 0
def is_tampered(self) -> bool     # (status & ZoneStatus.TROUBLE > 0) or (status & ZoneStatus.TAMPER > 0)
def is_low_battery(self) -> bool  # status & ZoneStatus.LOW_BATTERY > 0
def is_troubled(self) -> bool     # status & ZoneStatus.TROUBLE > 0
def is_triggered(self) -> bool    # status & ZoneStatus.TRIGGERED > 0
```

```python
for zone in location.zones.values():
    if zone.is_faulted() and zone.can_be_bypassed:
        print(f"{zone.description} is faulted and bypassable")
```

### `ZoneType` (`Enum`) and zone-type predicates

```python
from total_connect_client import ZoneType
```

`ZoneType` covers the "standard" Honeywell zone types (`SECURITY = 0`,
`ENTRY_EXIT1 = 1`, `FIRE_SMOKE = 9`, `CARBON_MONOXIDE = 14`, ... — see
`total_connect_client/const.py` and `ZONE_TYPES.md` for the full list and
what's actually been observed on real panels). A zone whose raw `ZoneTypeId`
isn't in this enum keeps that raw `int` in `zone_type_id` rather than raising.

```python
def is_type_button(self) -> bool
def is_type_security(self) -> bool
def is_type_motion(self) -> bool
def is_type_fire(self) -> bool           # heat or smoke
def is_type_temperature(self) -> bool
def is_type_carbon_monoxide(self) -> bool
def is_type_medical(self) -> bool
def is_type_keypad(self) -> bool
```

```python
for zone in location.zones.values():
    if zone.is_type_fire():
        print(f"smoke/heat sensor: {zone.description}")
```

### `zone.bypass()`

```python
def bypass(self) -> None
```

Convenience method: bypasses this zone via its parent location, but **only**
if `self.can_be_bypassed` is truthy — otherwise it silently does nothing (no
exception, no log line). Prefer `location.zone_bypass(zone.zoneid)` if you
want a failure to bypass a non-bypassable zone to actually raise.

---

## `TotalConnectDevice`

`from total_connect_client.device import TotalConnectDevice` — instances
come from `location.devices`, never construct one yourself.

| Attribute/property | Type | Description |
|---|---|---|
| `deviceid` | (raw JSON type, usually `int`) | Device identifier. |
| `name` | `str \| None` | Device name. |
| `class_id` | `int` | `DeviceClassID` — see `DEVICES.md` for the observed mapping to real hardware. |
| `serial_number` | (raw) | Device serial number, if provided. |
| `security_panel_type_id` | (raw) | `SecurityPanelTypeID`, if provided. |
| `flags` | `dict[str, str]` | Parsed `DeviceFlags`, including `PanelType`/`PanelVariant` used by `model_info()`. |
| `doorbell_info` | `dict[str, Any]` (property) | Set internally when `location.get_cameras()` finds a matching doorbell. Read/write both operate on the same internal field. |
| `video_info` | `dict[str, Any]` (property) | Same pattern, for VideoPIR devices. |
| `unicorn_info` | `dict[str, Any]` (property) | **Do not rely on reading this property.** The setter stores into a private `_unicorn_info` field, but the getter returns `_video_info` instead — reading `device.unicorn_info` gives you the device's video info, not what was last set via the `unicorn_info` setter. This is a source bug, not intended behavior; it is called out here so you don't lose time to it. |

```python
def is_doorbell(self) -> bool
```

Returns `True` if `doorbell_info["IsExistingDoorBellUser"] == 1`, **or** if
the device's raw (private) unicorn info has `DeviceVariant ==
"home.dv.doorbell"`. Note this checks the private field directly, not the
buggy `unicorn_info` property, so `is_doorbell()` itself is not affected by
the bug above.

```python
def model_info(self) -> tuple[str, str]
```

Returns `(model, model_id)` looked up from `(class_id, PanelType,
PanelVariant)` against a hardcoded table (see `DEVICES.md` for the source
data and `total_connect_client/device.py`'s `MODEL_LOOKUP`). Returns
`("Unknown model", "Unknown model ID")` and logs a warning for anything not in
the table — never raises.

```python
for device in location.devices.values():
    model, model_id = device.model_info()
    print(f"{device.name}: {model} {model_id}")
```

---

## `ArmingHelper` and `ArmType`

```python
from total_connect_client import ArmingHelper, ArmType
```

`ArmingHelper` wraps a `TotalConnectLocation` or `TotalConnectPartition` and
gives you named methods instead of `ArmType` enum members:

```python
class ArmingHelper:
    def __init__(self, partition_or_location: Any) -> None: ...
    def arm_away(self, usercode: str = "") -> None
    def arm_stay(self, usercode: str = "") -> None
    def arm_stay_instant(self, usercode: str = "") -> None
    def arm_away_instant(self, usercode: str = "") -> None
    def arm_stay_night(self, usercode: str = "") -> None
    def disarm(self, usercode: str = "") -> None
```

Each method just calls `self.armable.arm(arm_type=..., usercode=usercode)` /
`self.armable.disarm(usercode=usercode)` — same return/raise behavior as
`arm()`/`disarm()` documented above.

```python
ArmingHelper(location).arm_away()
ArmingHelper(partition).arm_stay_night()
```

### `ArmType` (`Enum`)

| Member | Value |
|---|---|
| `AWAY` | 0 |
| `STAY` | 1 |
| `STAY_INSTANT` | 2 |
| `AWAY_INSTANT` | 3 |
| `STAY_NIGHT` | 4 |

---

## `ArmingState`

```python
from total_connect_client import ArmingState
```

An `Enum` with one member per raw panel arming-state code (`DISARMED = 10200`,
`ARMED_AWAY = 10201`, `ARMING = 10307`, `ALARMING_CARBON_MONOXIDE = 10213`,
`UNKNOWN = 0`, and many ProA7-specific and bypass/instant/night variants — see
`total_connect_client/const.py` for the full list, several with issue-number
comments explaining why they exist). Rather than matching raw values yourself,
use the predicate methods:

| Predicate | True when |
|---|---|
| `is_disarmed()` | disarmed, disarmed-bypass, or disarmed-zone-faulted |
| `is_arming()` | in the process of arming |
| `is_disarming()` | in the process of disarming |
| `is_pending()` | `is_arming()` or `is_disarming()` |
| `is_armed_away()` | armed away, in any bypass/instant variant |
| `is_armed_home()` | armed stay, in any ProA7/bypass/instant variant, including `ARMED_STAY_OTHER` |
| `is_armed_night()` | armed stay-night in any variant — **also true for `ARMED_STAY_INSTANT` and `ARMED_STAY_INSTANT_BYPASS`**, per issue #240 (some panels report Night as Stay-Instant) |
| `is_armed_custom_bypass()` | `ARMED_CUSTOM_BYPASS` |
| `is_armed()` | any of `is_armed_away()`, `is_armed_home()`, `is_armed_night()`, `is_armed_custom_bypass()` |
| `is_triggered_police()` | `ALARMING` |
| `is_triggered_fire()` | `ALARMING_FIRE_SMOKE` |
| `is_triggered_gas()` | `ALARMING_CARBON_MONOXIDE` or its ProA7 variant |
| `is_triggered()` | any of the three `is_triggered_*` above |

```python
state = location.arming_state
if state.is_pending():
    print("still arming/disarming, check back shortly")
elif state.is_triggered():
    print("ALARM:", state)
```

---

## Exceptions

```python
from total_connect_client.exceptions import (
    TotalConnectError,
    AuthenticationError,
    InvalidSessionError,
    BadResultCodeError,
    FeatureNotSupportedError,
    RetryableTotalConnectError,
    PartialResponseError,
    UsercodeInvalid,
    UsercodeUnavailable,
    ServiceUnavailable,
    FailedToBypassZone,
)
```

### Hierarchy

```
TotalConnectError (Exception)
├── AuthenticationError
│   └── InvalidSessionError
├── BadResultCodeError
├── FeatureNotSupportedError
├── RetryableTotalConnectError
│   └── PartialResponseError
├── UsercodeInvalid
├── UsercodeUnavailable
├── ServiceUnavailable
└── FailedToBypassZone
```

Catching `TotalConnectError` catches everything this library raises on
purpose (it does not catch, e.g., a bare `requests.RequestException` escaping
past retries — see [Retries](#retries-and-reauthentication)).

### When each is raised, and what to do

| Exception | Raised when | Retryable by the library itself? | What a caller should do |
|---|---|---|---|
| `AuthenticationError` | Bad username/password, or `_ResultCode` is `BAD_USER_OR_PASSWORD`, `AUTHENTICATION_FAILED`, or `ACCOUNT_LOCKED`. | No — the client sets an internal "invalid credentials" flag and refuses to try authenticating again for this instance. | Stop. Don't retry with the same credentials; surface the error to the user. |
| `InvalidSessionError` (subclass of `AuthenticationError`) | HTTP 401, or `_ResultCode` is `INVALID_SESSION`/`INVALID_SESSIONID`. | **Yes, automatically**, inside `http_request` — the client calls `authenticate()` again and retries the request, up to `MAX_RETRY_ATTEMPTS` (5). | Usually nothing — you'll only see this escape if reauthentication itself failed after all retries (in which case it surfaces as `ServiceUnavailable`, not this). |
| `BadResultCodeError` | Any `_ResultCode` not otherwise mapped (the catch-all in `raise_for_resultcode`), including `COMMAND_FAILED` (e.g. "arm rejected, zone faulted") and a genuinely unrecognized numeric result code. | No. | Log the response and decide per-code; for `COMMAND_FAILED` specifically, check for a faulted zone before retrying an arm. |
| `FeatureNotSupportedError` | `_ResultCode.FEATURE_NOT_SUPPORTED` (`-120`). Note `get_zone_details()` catches this internally and only logs — it does not propagate from that call. | No. | The account/hardware doesn't support the call; don't retry it. |
| `RetryableTotalConnectError` | `_ResultCode` is `CONNECTION_ERROR`, `FAILED_TO_CONNECT`, `CANNOT_CONNECT`, or `BAD_OBJECT_REFERENCE`, **or** an HTTP status in `[429, 500, 502, 503, 504]`. | **Yes, automatically**, inside `http_request`, up to 5 attempts with `retry_delay` seconds between them. | Same as above — you'd only see this escape after retries are exhausted, and even then it surfaces wrapped as `ServiceUnavailable`. |
| `PartialResponseError` (subclass of `RetryableTotalConnectError`) | A response is missing a section it's always supposed to have — no `PanelStatus`, no `ArmingState`, no `PartitionID`, no `Partitions` list. The docstring calls these "rather frequent" because the TotalConnect servers are flaky. | **No** — despite the name and the parent class, these are raised *outside* `http_request`'s retry loop (from `location.py`'s `_update_status`/`_update_partitions`/`get_partition_details`), so nothing in this library retries them automatically. | The name says "retryable" in the sense that retrying the whole operation is a reasonable thing to do — but you, the caller, have to do that retry yourself (Home Assistant's integration does this at a higher level). |
| `UsercodeInvalid` | `_ResultCode.USER_CODE_INVALID` (`-4106`) — wrong usercode for an arm/disarm/bypass call. | No. | Prompt for/verify the usercode; don't blind-retry with the same value. |
| `UsercodeUnavailable` | `_ResultCode.USER_CODE_UNAVAILABLE` (`-4114`) — no usercode on file for this location/device, including the `"-1"` sentinel case documented above. | No. | Check that your `usercodes` dict actually covers this location. |
| `ServiceUnavailable` | The config endpoint didn't respond `ok`, or any retryable failure (network exception, or `RetryableTotalConnectError`/`InvalidSessionError`/`OAuth2Error`/`ValueError`) exhausted all retry attempts. | No — this **is** "retries exhausted." | Back off longer than `retry_delay` and try again later; check `https://status.resideo.com/`. |
| `FailedToBypassZone` | `_ResultCode.FAILED_TO_BYPASS_ZONE` (`-4504`) — the zone doesn't exist, or can't be bypassed (e.g. it's a smoke detector). | No. | Check `zone.can_be_bypassed` before calling bypass. |

### `ResultCode` → exception, from `raise_for_resultcode`

`raise_for_resultcode` is the single chokepoint most methods call after a
request. In order:

1. `SUCCESS` / `ARM_SUCCESS` / `DISARM_SUCCESS` / `SESSION_INITIATED` → returns, no exception.
2. Delegates to the retry check (`INVALID_SESSION`/`INVALID_SESSIONID` →
   `InvalidSessionError`; `CONNECTION_ERROR`/`FAILED_TO_CONNECT`/`CANNOT_CONNECT`/`BAD_OBJECT_REFERENCE`
   → `RetryableTotalConnectError`) — but by the time your own code calls
   `raise_for_resultcode` directly (most callers don't; `http_request` already
   handled the retryable cases), these are unlikely to still be present.
3. `BAD_USER_OR_PASSWORD` / `AUTHENTICATION_FAILED` / `ACCOUNT_LOCKED` → `AuthenticationError`.
4. `USER_CODE_UNAVAILABLE` → `UsercodeUnavailable`.
5. `USER_CODE_INVALID` → `UsercodeInvalid`.
6. `FEATURE_NOT_SUPPORTED` → `FeatureNotSupportedError`.
7. `FAILED_TO_BYPASS_ZONE` → `FailedToBypassZone`.
8. Anything else (including `COMMAND_FAILED`, `INVALID_PARAMETER`) → `BadResultCodeError`.

A numeric `ResultCode` that isn't in the `_ResultCode` enum at all raises
`BadResultCodeError` even earlier, from `_ResultCode.from_response()` itself.
See `RESULT_CODES.md` for the full catalogue of observed codes and what
triggers each.

### Retries and reauthentication

Full explanation with the request lifecycle diagram is in
[`architecture.md`](architecture.md#retry-and-reauthentication-model). Short
version: only the HTTP-status and `_ResultCode` values listed as "automatic"
above are retried inside the library, up to `MAX_RETRY_ATTEMPTS = 5` (a class
constant, not configurable) with `retry_delay` seconds between attempts
(default 6, set to `0` in tests). Everything else — including
`PartialResponseError` despite its parent class — is the caller's
responsibility to retry.
