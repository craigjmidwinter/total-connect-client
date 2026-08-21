# Developer guide

**Mode:** Tutorial + how-to, folded into one page (see the justification in
[`index.md`](index.md)). This page gets you from `pip install` to a working
arm/disarm loop against your own TotalConnect account. For exhaustive
signatures, parameters, and exceptions, see
[`api-reference.md`](api-reference.md). For *why* it's shaped this way, see
[`architecture.md`](architecture.md).

## Contributing to this repo

If you're working on `total-connect-client` itself (not just using it), copy
Home Assistant's development environment rather than inventing a new one:
follow <https://developers.home-assistant.io/docs/development_environment/>,
cloning this repo instead of Home Assistant's. You can also develop directly
on a Raspberry Pi or similar box if that's closer to your target environment.

## Using this library outside Home Assistant

Install it:

```bash
pip install total-connect-client
```

Import what you need:

```python
from total_connect_client import ArmingHelper, ArmType, TotalConnectClient
```

To arm or disarm a system you must provide the alarm's **usercode** (the code
you'd punch into the physical keypad — not your TotalConnect account
password). `usercodes` is a dict; each location looks up its own code by
location ID (as an `int` or a `str`), falling back to a `"default"` entry if
present. The full lookup rules — including what happens when nothing
matches — are in
[`api-reference.md`](api-reference.md#the-usercodes-dict--sharp-edges); the
short version for a single-location account is:

```python
usercodes = {"default": "1234"}
client = TotalConnectClient(username, password, usercodes)
```

`client.locations` is `dict[int, TotalConnectLocation]` — keyed by location
ID. To iterate the locations themselves, iterate `.values()`:

```python
for location in client.locations.values():
    # location.arming_state can be matched against the ArmingState enum members,
    # or you can call its convenience methods:
    location.arming_state.is_disarmed()
    location.arming_state.is_armed()          # true if armed in any way
    location.arming_state.is_armed_away()
    location.arming_state.is_pending()        # true if arming or disarming
    location.arming_state.is_triggered()      # true if in any alarm state
    location.arming_state.is_triggered_gas()  # true if in carbon monoxide alarm
    #    see api-reference.md for the full ArmingState predicate table

    # arm with one of the ArmType enum members, e.g.:
    #    location.arm(ArmType.STAY_INSTANT)
    # or, equivalently, use the named methods on ArmingHelper:
    #    ArmingHelper(location).arm_away()

    location.disarm()

    location.is_ac_loss()
    location.is_low_battery()
    location.is_cover_tampered()
    location.last_updated_timestamp_ticks
    location.configuration_sequence_number

    for zone_id, zone in location.zones.items():
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
        zone.is_type_fire()  # heat detector or smoke detector
        zone.is_type_carbon_monoxide()
        zone.is_type_medical()

        zone.partition  # the partition ID
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

        # bypass a specific zone you found faulted and bypassable, e.g.:
        if zone.is_faulted() and zone.can_be_bypassed:
            location.zone_bypass(zone_id)

    # to refresh a location
    location.get_partition_details()
    location.get_zone_details()
    location.get_panel_meta_data()

    # to arm or disarm by partition instead of the whole location
    for partition_id, partition in location.partitions.items():
        ArmingHelper(partition).arm_stay()
```

This is the same example that used to live here, corrected — see "What was
wrong with this example" below if you're curious what changed and why.
Construction can raise (bad credentials, unreachable service); see the
[minimal working example](api-reference.md#minimal-working-example) in the
API reference for the `try`/`except` shape you'll want around
`TotalConnectClient(...)` in real code.

## If you copied this example before August 2026

The example on this page was, for a long time, not runnable. If you copied it
and it failed, the fault was ours, not yours. Three things were wrong:

1. **`for location in client.locations:`** iterated the `dict`'s integer
   keys, not `TotalConnectLocation` objects — every subsequent
   `location.whatever` call would fail with `AttributeError: 'int' object has
   no attribute ...`. Fixed to `for location in client.locations.values():`.
2. **The partition loop ended with a bare `etc.`** — `partition_id, partition)
   in location.partitions.items(): ArmingHelper(partition).arm_stay(); etc.` —
   which is not valid Python (a trailing `.` with nothing after it is a
   `SyntaxError`, confirmed by parsing it with `ast.parse`). The whole
   example wouldn't even parse, let alone run. Removed.
3. **`location.zone_bypass(zoneid)`** referenced a variable `zoneid` that was
   never defined anywhere in the example — it would raise `NameError` if
   reached. Fixed by moving the bypass call inside the zone loop, where
   `zone_id` is an actual loop variable, and gating it on `is_faulted()` and
   `can_be_bypassed` so it reads as a real, sensible call rather than an
   unconditional one.

The corrected example above was verified end-to-end against mocked fixture
data (the same fixtures `tests/common.py`/`tests/const.py` use) to confirm it
actually executes without error — not just that it parses. It does.

The same `for location in client.locations:` line still appears in the module
docstring of `total_connect_client/client.py`. It has the same problem, and
correcting it is tracked separately from this documentation change.

## Recent and future interface changes

For the release-by-release list of what changed, see
[`../CHANGELOG.md`](../CHANGELOG.md). Structural notes about *why* the
interface looks the way it does — the partition-vs-location arming split, and
the `usercodes` `"-1"` sentinel fallback that may become a hard error in a
future release — are in
[`architecture.md`'s Interface evolution section](architecture.md#interface-evolution).

## Getting help

If there's something about the interface you don't understand, check the
[Home Assistant integration](https://github.com/home-assistant/core/blob/dev/homeassistant/components/totalconnect/)
that uses this package, or
[submit an issue](https://github.com/craigjmidwinter/total-connect-client/issues).

If you discover new status codes or other information this library doesn't
handle, please [submit an issue](https://github.com/craigjmidwinter/total-connect-client/issues)
— or, even better, a
[pull request](https://github.com/craigjmidwinter/total-connect-client/pulls).
