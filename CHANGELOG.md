# Changelog

All notable changes to `total_connect_client` are documented here. The format
is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this
project's versions follow a CalVer-ish scheme (`YYYY.M[.patch]`) rather than
semantic versioning.

> **Provenance note:** this file was reconstructed retroactively from GitHub
> Release notes and `git log`, starting with version `2025.1` (2025-01-21).
> Entries from `2025.1` through the current release are rewritten in
> user-facing terms from the original PR titles/descriptions, and — where
> those were too thin to tell what actually changed — from reading the
> commit diff directly. Versions before `2025.1` (back to the first `0.53`
> release in 2020) are summarized compactly under "Older releases" rather
> than reconstructed commit-by-commit; see the linked GitHub Releases for
> the original (auto-generated) notes on any of those.

## [Unreleased]

Mostly documentation, tests, and tooling. **One public API behavior change**
— the `TotalConnectDevice.unicorn_info` property, described under "Changed"
below. No logging or dependency changes.

### Fixed
- **`get_cameras()` no longer raises for Unicorn cameras.**
  `TotalConnectLocation._get_unicorn()` guarded on the key `"UnicornList"`
  and then read `"UnicornsList"`, which the API does not return — so
  `get_cameras()` raised `KeyError('UnicornsList')` for anyone owning one.
  The real response nests `UnicornList` inside `UnicornList`; the shape was
  recovered from issue #216 and is now pinned by the project's first camera
  fixture, `RESPONSE_CAMERA_LIST_UNICORN`.

### Changed
- **`TotalConnectDevice.unicorn_info` now returns unicorn info rather than
  video info.** Its getter returned `_video_info` while its setter wrote
  `_unicorn_info`, so reading the property gave you the device's VideoPIR
  data. **If you read `device.unicorn_info` and relied on receiving video
  data, switch to `device.video_info`.** Together with the `_get_unicorn()`
  fix above, unicorn data is now both retrieved and readable — previously
  neither worked. `is_doorbell()` was unaffected; it read the private field
  directly and was always correct.

### Added
- `CONTRIBUTING.md`, this `CHANGELOG.md`, and `SECURITY.md`.
- `docs/index.md`, `docs/api-reference.md` (the first full API reference this
  project has had — every public class, method, enum, and exception, with
  signatures, defaults, and what each error means), `docs/architecture.md`,
  and `docs/troubleshooting.md`.
- A pull request template, an issue-template config, and a feature-request
  form.
- 67 new tests covering arming, disarming, panel status, zone status, zone
  bypass, and the result-code-to-exception mapping. Coverage went from 71% to
  92%; `location.py`, which holds arm/disarm/panel status, went from 53% to
  92%.
- Python 3.14 in the CI matrix and the package classifiers.

### Fixed
- **The usage example in `docs/DEVELOPER.md` now runs.** It had three
  separate defects: `for location in client.locations:` iterated integer dict
  keys rather than location objects, a stray `etc.` inside the code fence made
  the whole block a `SyntaxError`, and `location.zone_bypass(zoneid)`
  referenced a variable that was never defined. If you copied that example and
  it failed, that was our bug.
- README install instructions now create a virtual environment first. The
  previous bare `pip install total-connect-client` fails outright on any
  PEP 668 Python (current Homebrew, Debian, and Fedora defaults).
- Documented that `python3 -m total_connect_client` writes a `test.log` file
  containing `DEBUG`-level request and response data, and corrected the
  README's warning about what that output exposes — the password is redacted;
  the username, identifiers, and (for library callers) usercodes are not.
- Documented the Python 3.10 minimum in prose. On Python 3.9, `pip` silently
  installs the 2024.4 SOAP-era release instead of reporting an error.
- CI no longer installs a `.[dev]` extra that does not exist, and its tox
  environment names now match those declared in `pyproject.toml`.
- Removed a stray empty `__init__.py` from the repository root, after
  confirming the built wheel and sdist are byte-identical without it.

## [2026.7] - 2026-07-06

### Added
- `device.py` gained a lookup that maps a panel's model name (e.g. "Lynx
  Touch") to its model ID (e.g. "L7000"), for use by consumers like Home
  Assistant that want to display panel model information.
  ([#296](https://github.com/craigjmidwinter/total-connect-client/pull/296))

### Fixed
- Improved error handling in `get_configuration()` for malformed or
  unexpected responses from TotalConnect.
  ([#297](https://github.com/craigjmidwinter/total-connect-client/pull/297))

### Changed
- Dependency updates and `pyproject.toml` maintenance.
  ([#297](https://github.com/craigjmidwinter/total-connect-client/pull/297))

## [2025.12.2] - 2025-12-31

### Fixed
- Zone bypass no longer requires a zone to already be showing as faulted
  before it can be bypassed — some zones can legitimately be bypassed while
  not currently faulted, and the earlier check rejected those.
  ([#295](https://github.com/craigjmidwinter/total-connect-client/pull/295))

## [2025.12.1] - 2025-12-31

### Fixed
- Fixed handling of the bypass API response: TotalConnect can return success
  (ResultCode 0) for a bypass call while still reporting the zone's status as
  "normal" rather than "bypassed" — the next full panel status update shows
  the bypass correctly. The client no longer trusts the bypass call's own
  response to mark a zone bypassed.
  ([#294](https://github.com/craigjmidwinter/total-connect-client/pull/294))

## [2025.12] - 2025-12-31

### Added
- Experimental `RemotePanicAlarm` call, added as a manual/live-test script
  under `total_connect_client/live/trigger.py` to explore whether the REST
  API can trigger the panel programmatically. Not part of the supported
  public API.
  ([#288](https://github.com/craigjmidwinter/total-connect-client/pull/288))

### Fixed
- Additional error checking around zone bypass, fixing a case where bypass
  calls could fail.
  ([#292](https://github.com/craigjmidwinter/total-connect-client/pull/292))

### Changed
- Documentation improvements to the developer docs, and a new GitHub bug
  report issue template.
  ([#286](https://github.com/craigjmidwinter/total-connect-client/pull/286),
  [#289](https://github.com/craigjmidwinter/total-connect-client/pull/289),
  [#290](https://github.com/craigjmidwinter/total-connect-client/pull/290))
- Project tooling modernized: dependency groups in `pyproject.toml`, updated
  GitHub Actions workflows, and a round of typing fixes across the codebase.
  ([#293](https://github.com/craigjmidwinter/total-connect-client/pull/293))

## [2025.8] - 2025-09-01

### Changed
- Merged the `all_rest_api` development branch into `master` — the REST API
  rewrite (see `2025.5` below) became the only code path; the legacy SOAP
  client that had been kept alongside it during the transition was removed.
  ([#284](https://github.com/craigjmidwinter/total-connect-client/pull/284))

### Fixed
- Older-generation Vista panels that report the legacy "STAY_INSTANT"
  arming status code now have that status surfaced as Night, matching what
  those panels actually do.

## [2025.5] - 2025-05-04

### Changed
- **Major rewrite:** the library now speaks TotalConnect's
  [REST API](https://rs.alarmnet.com/TC2API.TCResource/) instead of the
  legacy [SOAP API](https://rs.alarmnet.com/TC21api/tc2.asmx). This touched
  authentication, location/zone/partition loading, and arm/disarm/bypass
  calls throughout the client. The maintainers described this release as
  tested over several months but likely to still have edge-case bugs, and
  asked users to file issues for anything unexpected.
- New OAuth2-based authentication flow, replacing the previous
  username/password SOAP login.
  ([#243](https://github.com/craigjmidwinter/total-connect-client/pull/243),
  [#255](https://github.com/craigjmidwinter/total-connect-client/pull/255))
- HTTP requests now retry automatically based on response status code (429,
  500, 502, 503, 504).
  ([#274](https://github.com/craigjmidwinter/total-connect-client/pull/274))

### Fixed
- Handling for ResultCode `-4108`.
  ([#267](https://github.com/craigjmidwinter/total-connect-client/pull/267))

This release folds in the `2025.2.rc1` through `2025.2.rc6` pre-releases,
which tracked incremental progress on the rewrite above; they are not listed
separately here since `2025.5` is what actually shipped.

## [2025.1.4] - 2025-01-28

### Changed
- Simplified how Home Assistant's own test suite mocks this client, to make
  future Home Assistant-side testing easier.
  ([#248](https://github.com/craigjmidwinter/total-connect-client/pull/248))

## [2025.1.3] - 2025-01-27

### Changed
- User-code validation can now use the alternative `ValidateUserCodeEx`
  request.
  ([#246](https://github.com/craigjmidwinter/total-connect-client/pull/246))

## [2025.1.2] - 2025-01-27

### Changed
- New authentication scheme.
  ([#243](https://github.com/craigjmidwinter/total-connect-client/pull/243))

## [2025.1] - 2025-01-21

### Added
- `arm()` and `disarm()` now accept an optional `usercode` parameter, so a
  usercode can be supplied per call instead of only through the client's
  `usercodes` dictionary.
  ([#238](https://github.com/craigjmidwinter/total-connect-client/pull/238))

### Changed
- Improved type annotations throughout, including for `partition_id`.
  ([#237](https://github.com/craigjmidwinter/total-connect-client/pull/237),
  [#239](https://github.com/craigjmidwinter/total-connect-client/pull/239))

## Older releases (2020–2024)

<details>
<summary>Compact summary — see individual <a href="https://github.com/craigjmidwinter/total-connect-client/releases">GitHub Releases</a> for the original notes on any version</summary>

- **2024.12.1, 2024.12** — Added a CI workflow and PyPI publishing on GitHub
  Release; fixed an authentication error; handled ResultCode `-123` and a
  `None` response code; updated the `zeep` SOAP dependency; initial typing
  and linter cleanup.
- **2024.5, 2024.4** — Cached the SOAP WSDL file locally (avoiding a runtime
  fetch); handled ArmingState code `10215`.
- **2023.12.1, 2023.12.0, 2023.11.1, 2023.11** — Fixed an issue affecting
  doorbell device handling; updated the Z-Wave test script.
- **2023.7, 2023.2** — Added zone bypass support (`zone.bypass()`,
  `bypass_all()`, `clear_bypass()`) with tests; added panel sync/status
  calls; improved handling when a location reports no zones on startup.
- **2023.1** — Updated the project's build/test setup; fixed a Python 3.10
  SSL error.
- **2022.10** — Fixed a recurring connection loss that happened roughly
  every 5 hours; added a `ZoneStatus` value for communication failure;
  updated retry request arguments after re-authentication.
- **2022.5, 2022.3, 2022.2.1, 2022.2** — Handling for additional ProA7 panel
  status codes, based on user-submitted system data.
- **2022.1** — Handling for unknown `ZoneStatus` values and ArmingState code
  `10230`.
- **2021.12** — Added `FeatureNotSupportedError`, raised by
  `get_zone_details()` when the account/hardware doesn't support it.
- **2021.11.5 – 2021.11** — Fixed a bug in `partition_list` handling that
  prevented arming/disarming individual partitions; added a helper to force
  location reloading for Home Assistant; updated the `zeep` dependency.
- **2021.10** — Adjusted retry timing to reduce server load and improve
  success rate; loaded more partition detail where available.
- **2021.8.3 – 2021.8** — Partition-related bug fixes and additional zone
  type handling.
- **2021.7.1, 2021.07 ("Multi-Partition Support")** — Added support for
  systems with multiple partitions.
- **0.58, 0.55.6, v0.53 (2020–2021)** — Early releases predating the current
  CalVer versioning scheme. Not reconstructed in detail here.

</details>
