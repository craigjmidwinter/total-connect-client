# total-connect-client

**A Python client for Total Connect 2 (Resideo/Honeywell) alarm systems — arm, disarm, bypass zones, and read panel/zone status.**

Resideo publishes an [incomplete generated API reference](https://rs.alarmnet.com/TC2API.TCResource/) for Total Connect 2, but it omits many endpoint details and result-code semantics and provides no verified third-party SDK or compatibility contract. This library reverse-engineers the REST backend the official web and mobile apps use, and is the library the Home Assistant `totalconnect` integration is built on.

[![CI](https://github.com/craigjmidwinter/total-connect-client/actions/workflows/python-package.yml/badge.svg)](https://github.com/craigjmidwinter/total-connect-client/actions/workflows/python-package.yml)
[![PyPI](https://img.shields.io/pypi/v/total-connect-client)](https://pypi.org/project/total-connect-client/)
[![Python versions](https://img.shields.io/pypi/pyversions/total-connect-client)](https://pypi.org/project/total-connect-client/)
[![License: MIT](https://img.shields.io/pypi/l/total-connect-client)](LICENSE)

## Why this exists

Resideo's [generated Total Connect 2 API reference](https://rs.alarmnet.com/TC2API.TCResource/) is incomplete: it omits many endpoint details and result-code semantics and provides no verified third-party SDK or compatibility contract. Home Assistant's `totalconnect` integration needs a client anyway, so this library reverse-engineers the same REST backend the official web and mobile apps talk to (`rs.alarmnet.com`) — reading real traffic, testing against real panels, and writing down what was found. The result-code catalogue in [`docs/RESULT_CODES.md`](docs/RESULT_CODES.md), the zone-type table in [`docs/ZONE_TYPES.md`](docs/ZONE_TYPES.md), and the device/model table in [`docs/DEVICES.md`](docs/DEVICES.md) fill gaps in that generated reference with data this project's users submitted from their own accounts and hardware.

Started by [@craigjmidwinter](https://github.com/craigjmidwinter) to add alarm support to his own Home Assistant setup; actively maintained today by [@austinmroczek](https://github.com/austinmroczek) with contributions from others. Ships on [PyPI as `total-connect-client`](https://pypi.org/project/total-connect-client/).

**Before you go further, know the one hard requirement:** everything this library does — the CLI diagnostic tool, every code example below, every test-suite claim — talks to a real, live TotalConnect account. There is no demo mode, no offline sandbox, and no fixture mode exposed to consumers (the test suite mocks HTTP internally with recorded fixtures, but that mode isn't something you can point this library at from the outside). **If you don't have an active TotalConnect monitoring subscription and a panel enrolled in it, this library cannot do anything visible for you** — not "a limited demo," nothing. If that's you, read on for what the library does and how it's shaped, then come back once you have an account. If you do have one, the [Quickstart](#quickstart) below gets you to a real result.

## What running it actually looks like

Two real, unedited captures — a clean install via [`uv`](https://docs.astral.sh/uv/), and the CLI's own usage/error output. Neither requires an account; both are exactly what the commands print.

```console
$ uv venv && uv pip install total-connect-client
Resolved 9 packages in 540ms
Installed 9 packages in 8ms
```

```console
$ python3 -m total_connect_client
usage:  python3 -m total_connect_client username [password]
```

That second one matters more than it looks: the CLI validates its arguments before anything else, so a bad invocation fails in milliseconds with the exact fix, not a stack trace. A *good* invocation (real username, real TotalConnect account) makes a live authenticated call — with a wrong password, that same command reaches TotalConnect's servers and comes back with a real, typed exception instead of a generic error:

```console
$ python3 -m total_connect_client not-a-real-user@example.invalid
Password:
Traceback (most recent call last):
  ...
total_connect_client.exceptions.AuthenticationError: ('AUTHENTICATION_FAILED', {'error': '-100', 'error_description': 'Authentication Failed'})
```

(The `...` elides real stack frames not reproduced here — the final line is the verbatim exception.) `AuthenticationError` is one of eleven exception types this library raises on purpose; see [`docs/api-reference.md`'s exceptions table](docs/api-reference.md#exceptions) for what each one means and what to do about it. We don't have a captured successful-authentication session to show here — producing one would need a real account, which we don't have — so we're not showing you a fabricated one. See "Before you go further" above.

## What it does

- **Arming** — away, stay, stay-instant, away-instant, and stay-night, at the location level or scoped to one partition. `ArmType` enum and `ArmingHelper` convenience methods: [`docs/api-reference.md#armtype-enum`](docs/api-reference.md#armtype-enum). Tested in `tests/test_location.py` (`test_arm_away_sends_arm_type_and_usercode_then_panel_reports_armed_away`, `test_arm_stay_night_sends_arm_type_and_usercode_then_panel_reports_armed_night`, and others).
- **Disarming** — location- or partition-scoped, a documented no-op if already disarmed/disarming. `tests/test_location.py::test_disarm_with_invalid_usercode_raises_usercode_invalid`.
- **Panel status** — armed/disarmed/arming/disarming/triggered state via `ArmingState`, plus AC-loss, low-battery, and cover-tamper flags. `tests/test_location.py::test_get_panel_meta_data_raises_partial_response_error_when_arming_state_missing` and neighboring tests exercise the parsing; predicate methods documented in [`docs/api-reference.md#armingstate`](docs/api-reference.md#armingstate).
- **Zone status** — normal, bypassed, faulted, trouble, tamper, communication failure, low battery, and triggered, as an `IntFlag`. Requires "Sensor Activities" enabled on your TotalConnect account for fault status specifically — see [Notes that bite people](#notes-that-bite-people) below. `tests/test_zone.py::test_proa7_zones`, `test_unknown_status`.
- **Zone bypass** — single zone, all faulted zones, or clear all bypasses. `tests/test_location.py::test_zone_bypass_sends_zone_id_and_usercode`, `test_zone_bypass_all_only_bypasses_faulted_zones_that_allow_it`, `test_clear_bypass_sends_usercode_when_zones_are_bypassed`.
- **Device and panel model lookup** — maps raw `DeviceClassID`/`PanelType`/`PanelVariant` values to real hardware model names, from [`docs/DEVICES.md`](docs/DEVICES.md)'s field-tested table. `tests/test_device.py`.
- **Automatic retry and reauthentication** — transient failures and expired sessions are retried and re-authenticated inside the library, without you writing that logic. Documented in [`docs/architecture.md#retry-and-reauthentication-model`](docs/architecture.md#retry-and-reauthentication-model); `tests/test_client.py::test_get_panel_meta_data_reauthenticates_after_invalid_session_then_succeeds`, `test_http_request_retries_on_retryable_result_code_then_succeeds`.
- **An empirical result-code catalogue** — [`docs/RESULT_CODES.md`](docs/RESULT_CODES.md), built from real accounts because Resideo's generated API reference omits result-code semantics.

Not built: a camera-streaming client (device metadata for cameras is read, streaming is not implemented), custom-arming profiles (`arm_custom()` and `get_custom_arm_settings()` exist as placeholders and unconditionally raise), and anything beyond the endpoints listed above — there is no general-purpose TotalConnect API wrapper here, only what arm/disarm/status/bypass/cameras/panic needs.

## Who this is for

- **The Home Assistant user** who wants their Total Connect alarm to show up in their dashboard. You don't need this library directly — install the [Home Assistant `totalconnect` integration](https://www.home-assistant.io/integrations/totalconnect/), which already depends on this package. Come back here only if that integration is misbehaving and its issue tracker points you at this repo.
- **The developer** automating something against TotalConnect outside Home Assistant — a script, a different home automation system, a personal dashboard. This library is for you; start at [Quickstart](#quickstart).
- **The maintainer (or contributor) diagnosing a panel model nobody on the project owns.** [`docs/DEVICES.md`](docs/DEVICES.md), [`docs/RESULT_CODES.md`](docs/RESULT_CODES.md), and [`docs/ZONE_TYPES.md`](docs/ZONE_TYPES.md) exist because past contributors submitted diagnostic output from hardware the maintainers don't have. See [`CONTRIBUTING.md`](CONTRIBUTING.md) if that's you.

## Alternatives

| Instead of this library | Use it instead when |
|---|---|
| [Home Assistant `totalconnect` integration](https://www.home-assistant.io/integrations/totalconnect/) | You just want your alarm in Home Assistant and don't want to write Python — the integration already wraps this library for you. |
| [Total Connect 2 web portal](https://totalconnect2.com) / the Total Connect mobile app | You want a supported, vendor-backed interface and have no need for programmatic access. |
| Direct REST calls against TotalConnect's API, using this project's [`docs/`](docs/index.md) as a map | You need an endpoint this library doesn't wrap (its coverage is arm/disarm/status/bypass/zone-bypass/cameras/panic — see [`docs/api-reference.md`](docs/api-reference.md)), and you're willing to work from reverse-engineered field notes alongside an incomplete vendor reference. |

## Install

**Requires Python 3.10 or newer** (`requires-python = ">=3.10"` in `pyproject.toml`). This matters more than it sounds: on Python 3.9, `pip install total-connect-client` **succeeds with no warning** but silently resolves to `2024.4` — a release over two years old, built on the deprecated SOAP/`zeep` transport this library replaced in `2025.5`. There is no runtime check that stops this. If a fresh install imports `zeep` or otherwise looks nothing like the docs on this page, you're on an unsupported interpreter; upgrade Python and reinstall.

### From PyPI (primary path)

Create a virtual environment first. Skipping this step is the single most common install failure for this project: on any current, unmodified Python (stock Homebrew on macOS, Debian/Ubuntu ≥ 23.04, Fedora ≥ 38 — i.e. most machines someone would reach for today), running `pip install` directly against the system interpreter fails immediately with [PEP 668](https://peps.python.org/pep-0668/)'s guard:

```console
$ python3 -m pip install total-connect-client
error: externally-managed-environment

× This environment is externally managed
╰─> To install Python packages system-wide, try brew install
    xyz, where xyz is the package you are trying to
    install.

    If you wish to install a Python library that isn't in Homebrew,
    use a virtual environment:

    python3 -m venv path/to/venv
    source path/to/venv/bin/activate
    python3 -m pip install xyz
    ...
note: If you believe this is a mistake, please contact your Python installation or OS distribution provider. You can override this, at the risk of breaking your Python installation or OS, by passing --break-system-packages.
hint: See PEP 668 for the detailed specification.
```

That message is pip's own, not this project's, and it's correct — the fix is the venv it describes:

```bash
python3 -m venv .venv
source .venv/bin/activate   # .venv\Scripts\activate on Windows
python3 -m pip install total-connect-client
```

If you use [`uv`](https://docs.astral.sh/uv/), the same result is faster and skips the PEP 668 guard entirely (measured on a warm cache):

```console
$ uv venv && uv pip install total-connect-client
Resolved 9 packages in 540ms
Installed 9 packages in 8ms
```

### From source (contributors)

See [`CONTRIBUTING.md`](CONTRIBUTING.md#setup) for the editable-install setup used for development — it also installs the test/lint/type-check tooling this project uses.

### Upgrade

```bash
python3 -m pip install --upgrade total-connect-client
```

### Uninstall

```bash
python3 -m pip uninstall total-connect-client
```

This removes everything `pip` installed — no leftover files in `site-packages`. It does **not** remove `test.log`, a file the diagnostic CLI (see below) writes to your current working directory on every run. `pip` never knew that file existed; delete it yourself if you created one.

## Quickstart

**Prerequisite:** an active TotalConnect account with a monitoring subscription, and a panel enrolled in it. Without both of those, stop here — see "Before you go further" above.

Measured 2026-08-21 on macOS with a warm `uv` cache: creating a venv and installing takes under 5 seconds, and the CLI reaching TotalConnect's servers and getting a real (if unhelpful, with a wrong password) response back takes about 5 more — under 30 seconds mechanically. We did not measure the remaining step — a real login against a real account — because doing so would have required using someone's real credentials, which we deliberately avoided (see [`SECURITY.md`](SECURITY.md)). Budget a few minutes total; the bottleneck is TotalConnect's own servers, not this library.

1. **Create a virtual environment and install** (see [Install](#install) above for the PEP 668 and Python-3.9 caveats):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   python3 -m pip install total-connect-client
   ```

2. **Run the diagnostic CLI against your own account**, substituting your TotalConnect username:

   ```bash
   python3 -m total_connect_client you@example.com
   ```

   You'll be prompted for your password interactively (not echoed to the terminal, not passed as an argument — see the security note below on why the argument form is worth avoiding).

3. **Expected output on success:** the library authenticates, loads every location's partitions/zones/panel status, then `TotalConnectClient.__str__` prints your username, `Password: [hidden]`, a usercodes dict (empty for this CLI — it constructs the client without usercodes), and a listing of your locations, devices, partitions, and zones, followed by a `times_as_string()` breakdown of how long each phase took. We are not reproducing a captured example of that output here — we have no real account to capture it from — but the shape above is exactly what `total_connect_client/client.py`'s `__str__` method produces; nothing is hidden from you beyond the password.

4. **This also writes `test.log`.** Every invocation of the CLI — success, failure, or a bare usage error — silently creates or appends to a `test.log` file in your current directory containing full `DEBUG`-level logs. See the warning below before you share anything from this run.

**WARNING — read before sharing any output from step 2–4 with anyone, developers included:** the terminal output does **not** hide your username, your location/device/zone identifiers, or — if you print a client you constructed yourself with usercodes — your alarm usercodes. Only the password is redacted (`Password: [hidden]`). `test.log` is worse: at `DEBUG` level it additionally contains every HTTP request and response the client made, including the usercode sent on any arm/disarm/bypass call and potentially the OAuth access/refresh token TotalConnect issued for your session. Redact your username and every usercode from both before posting either. Full detail on what's exposed and why: [`SECURITY.md`](SECURITY.md). Task-oriented walkthrough with more on capturing and redacting diagnostics: [`docs/troubleshooting.md`](docs/troubleshooting.md).

For the fuller developer walkthrough — arming, reading zone status, bypassing zones, handling exceptions — see [`docs/DEVELOPER.md`](docs/DEVELOPER.md).

## Configuration and usage reference

`TotalConnectClient(username, password, usercodes=None, auto_bypass_battery=False, retry_delay=6, load_details=True)` is the entry point; constructing it logs in immediately. Full parameter table, every method's signature/returns/raises, and the complete exception hierarchy: [`docs/api-reference.md`](docs/api-reference.md).

| Parameter | Default | What it's for |
|---|---|---|
| `username`, `password` | required | Your TotalConnect **account** credentials — not the alarm keypad code. |
| `usercodes` | `None` | Maps a location to the alarm keypad usercode used for arm/disarm/bypass. See below — the lookup is more particular than the type hint suggests. |
| `auto_bypass_battery` | `False` | Auto-bypass low-battery zones as data refreshes. Stored as `self.auto_bypass_low_battery` — a different name than the constructor argument; see [`docs/api-reference.md`](docs/api-reference.md#totalconnectclientusername-password-usercodesnone-auto_bypass_batteryfalse-retry_delay6-load_detailstrue) if you introspect the instance. |
| `retry_delay` | `6` (seconds) | Delay between automatic retry attempts on a retryable failure. |
| `load_details` | `True` | If `True`, fetches every location's partitions/zones/panel status before the constructor returns (can be a dozen-plus HTTP round-trips for a multi-location account). Set `False` to get a fast-returning client and fetch details yourself, lazily. |

### Notes that bite people

- **`client.locations` is a `dict[int, TotalConnectLocation]`, keyed by location ID — not a list.** `for location in client.locations:` iterates the integer keys, not location objects, and every `location.whatever` call after that raises `AttributeError`. Iterate `client.locations.values()` instead. (This exact mistake was in this project's own published example for years; see `docs/DEVELOPER.md`'s "What was wrong with this example" section.)
- **The `usercodes` dict has a silent fallback you should know about.** For each location, the client tries the location ID as an `int` key, then as a `str` key, then a `"default"` key. If none match, it does **not** raise — it silently sets that location's usercode to the sentinel `"-1"`, and any subsequent arm/disarm/bypass call fails later with `UsercodeInvalid`/`UsercodeUnavailable` instead of failing clearly at construction time. If you support multiple locations, make sure every one is covered by `usercodes` or a `"default"` entry. Full detail: [`docs/api-reference.md`'s usercodes section](docs/api-reference.md#the-usercodes-dict--sharp-edges).
- **`get_zone_details()` fails on the first attempt essentially every time, and succeeds on the automatic retry.** This is normal TotalConnect server behavior, not a bug in your code — the client already retries `CONNECTION_ERROR` internally, so you don't have to, but expect to see it in logs on every call. See [`docs/REST_NOTES.md`](docs/REST_NOTES.md).
- **Zone-fault status needs "Sensor Activities" turned on for your account.** Without it, `zone.is_faulted()` won't reflect open sensors even though the rest of zone status works. Your monitoring company may charge an extra fee to enable it — Total Connect 2 web portal: **Notifications → Sensor Activities**; mobile app: **More → Settings → Notifications → Sensor Activities**.
- **A successful `zone_bypass()`/`zone_bypass_all()` doesn't update the zone's in-memory status.** TotalConnect's own bypass response reports success while still showing the zone as "normal" — only the next `get_panel_meta_data()` or `get_zone_details()` call reflects the bypass. Don't assert `zone.is_bypassed()` immediately after bypassing; refresh first.
- **The diagnostic CLI writes `test.log` unconditionally, and it's more sensitive than the terminal output.** See the Quickstart warning above and [`SECURITY.md`](SECURITY.md).

## Architecture

```
total_connect_client/       The library (this is what ships to PyPI and what
                             Home Assistant's integration imports).
  client.py                   TotalConnectClient — auth, HTTP transport, retries.
  location.py                  TotalConnectLocation — arm/disarm/bypass, status.
  partition.py, zone.py,        Per-partition arm/disarm; zone status/type; device
  device.py, user.py            metadata; the authenticated user's own info.
  const.py, exceptions.py       Endpoints/enums/internal result codes; the public
                                 exception hierarchy.
  __main__.py                   The `python3 -m total_connect_client` CLI.
  live/                         Manual scripts maintainers run against a real
                                 panel by hand — never invoked by tests or CI.
tests/                       The suite — entirely against recorded/mocked
                             fixtures, no real network access.
docs/                        Reference and how-to material — start at docs/index.md.
```

Full annotated layout, including `tests/` and `.github/`, and the invariants a PR must not break: [`CONTRIBUTING.md`](CONTRIBUTING.md#repo-layout). *Why* the client is shaped this way — the auth flow, the retry/reauthentication model — is in [`docs/architecture.md`](docs/architecture.md).

## Contributing

Contributions are welcome, especially fixture data from panels the maintainers don't own — the result-code and device tables in `docs/` exist because past contributors submitted exactly that. See [`CONTRIBUTING.md`](CONTRIBUTING.md) for setup, the test/lint/type-check commands, and the invariants a PR needs to respect (this library's main consumer, Home Assistant, treats its public API and exception hierarchy as a contract).

## Status

Actively maintained. Latest release is `2026.7` (2026-07-06); releases follow a CalVer-style scheme (`YYYY.M[.patch]`), not semantic versioning, and there is no 1.0 milestone planned — the project has been in continuous use since 2020. As measured on a clean checkout (2026-08-21): 106 tests pass, `ruff check`/`ruff format --check` are clean, `mypy --strict` is clean, and test coverage is 92% (`location.py`, the module holding arm/disarm/panel status, is at 92%; `client.py` at 88% is the weakest library module, and the `__main__.py` CLI script is untested). API stability matters here more than the version scheme implies: Home Assistant's `totalconnect` integration imports this package's public classes and exception types directly, so breaking changes are called out explicitly rather than shipped quietly (see [`CONTRIBUTING.md`'s invariants](CONTRIBUTING.md#invariants-a-pr-must-not-break)). Total Connect 2's backend has an incomplete generated vendor reference but no stated third-party compatibility contract, so this library still reverse-engineers omitted details; the backend can and has changed without notice, which is why this project keeps asking users for diagnostic output rather than working from a complete spec.

## License and credits

[MIT License](LICENSE). Copyright (c) 2019 Craig J. Midwinter.

Started by [@craigjmidwinter](https://github.com/craigjmidwinter); actively maintained by [@austinmroczek](https://github.com/austinmroczek); built on contributions — including the field-tested data in `docs/` — from many others. Runtime dependencies: [`pycryptodome`](https://pypi.org/project/pycryptodome/) (RSA credential encryption) and [`requests-oauthlib`](https://pypi.org/project/requests-oauthlib/) (the OAuth2 password-grant flow) — exactly two, both actively maintained as of August 2026.
