# Contributing to total-connect-client

Thanks for looking at this. Welcome.

## The one thing to understand first

**You cannot meaningfully test this library against a real alarm system.**
Nobody on this project has access to your panel, your account, or your
usercodes, and the TotalConnect servers are not something we can point CI at.
So the entire test suite is built on *recorded* API responses — JSON
payloads captured from real accounts, sanitized, and checked into
`tests/const.py` (currently about 1,500 lines of fixtures). Every test mocks
HTTP with those recordings via `requests_mock`; nothing in `pytest` ever talks
to `totalconnect2.com`.

This has two consequences that shape everything else in this document:

1. **If you're fixing a bug tied to your specific panel, the fastest path to
   a merged PR is a new fixture**, not a description of the symptom. If you
   can add the actual response your panel/account produced (with your
   username, password, usercode, and any account/device IDs replaced by
   placeholders) as a new case in `tests/const.py` and a test that exercises
   it, you have effectively given the maintainers eyes on hardware they don't
   own.
2. **This is why issues ask for your system's data.** When a maintainer asks
   you to run the command-line diagnostic tool and attach the output, they
   are asking for the next fixture. See [SECURITY.md](SECURITY.md) for what
   to scrub before you do that — usercodes and account/device IDs do not
   belong in a public issue.

## Setup

Verified on a clean checkout, macOS, CPython 3.14.2. Any currently-supported
Python from 3.10 up should work (see `requires-python` in `pyproject.toml`).

```bash
uv venv && uv pip install -e . --group dev
uv run --group dev pytest -q
```

If that isn't green on a clean checkout, that is a bug in this repo — please
open an issue rather than assuming your environment is at fault.

If you don't have [`uv`](https://docs.astral.sh/uv/) installed, the
equivalent with plain `pip` is:

```bash
python3 -m venv .venv
source .venv/bin/activate   # .venv\Scripts\activate on Windows
python3 -m pip install --upgrade pip     # --group needs pip 25.1 or newer
pip install -e . --group dev
pytest -q
```

`--group` is [PEP 735](https://peps.python.org/pep-0735/) dependency-group
support, which **pip only understands from 25.1 onward** — verified by
testing: pip 25.0 does not recognize the flag, pip 25.1 does. This project has
no `[project.optional-dependencies]` table, so `pip install -e .[dev]` does
not work and never has; if you are on an older pip, upgrade it rather than
looking for an extra that does not exist.

### Commands

| Command | What it runs |
| --- | --- |
| `uv run --group dev pytest -q` | The full test suite (`tests/`) against the recorded-response fixtures. No network access. |
| `uv run --group lint ruff check total_connect_client tests` | Linting: pyflakes, pycodestyle, import sort, bugbear, comprehensions, pyupgrade (see `[tool.ruff.lint]` in `pyproject.toml` for the exact rule set). |
| `uv run --group lint ruff format --check total_connect_client tests` | Formatting check only — run without `--check` to have `ruff` reformat in place. |
| `uv run --group type mypy -p total_connect_client` | Type checking with `mypy --strict` over the library package (not `tests/`). |
| `uv run --group coverage coverage run -m pytest && uv run --group coverage coverage report` | Test run instrumented for coverage, then a summary. Current total is around 71%; `total_connect_client/live/*.py` is intentionally excluded (see below). |

If you don't have `uv`, the same commands work by activating the venv above
and dropping the `uv run --group <name>` prefix (e.g. `pytest -q`, `ruff
check total_connect_client tests`, `mypy -p total_connect_client`) — install
whichever dependency group you need first with
`pip install -e . --group <name>`.

### The CI path: tox

CI does **not** run the `uv` commands above directly — it drives
[`tox`](https://tox.wiki/), configured in the `[tool.tox]` tables of
`pyproject.toml`. If you want to reproduce what CI actually does:

```bash
pip install tox
tox -e py312          # run the test suite on a specific interpreter (py310/py311/py312/py313)
tox -e lint            # ruff check + ruff format --check
tox -e type             # mypy --strict
tox -e coverage          # coverage run + report
```

`tox` builds its own isolated environments per target, so it's slower than
the `uv run` commands above but is the closest thing to what GitHub Actions
runs on every PR (`.github/workflows/python-package.yml`). If a `uv`-based
run and a `tox`-based run disagree, treat the `tox` result as authoritative
and say so in your PR — that mismatch is itself worth reporting.

## Repo layout

```
total_connect_client/       The library. This is what ships to PyPI and what
                             Home Assistant's `totalconnect` integration imports.
  __init__.py                Public API surface: TotalConnectClient, ArmingHelper,
                              ArmType, ArmingState, ZoneType, ZoneStatus, ResultCode.
  client.py                  TotalConnectClient — auth, HTTP transport, retries,
                              the top-level object every consumer instantiates.
  location.py                TotalConnectLocation — arm/disarm/bypass, panel and
                              zone status for one alarm location.
  partition.py                TotalConnectPartition — per-partition arm/disarm.
  device.py                   Device metadata (panel model/model ID lookups).
  zone.py                     TotalConnectZone — zone status, type, and the
                               ZoneStatus/ZoneType enums.
  user.py                     TotalConnectUser — the authenticated user's info.
  const.py                    Endpoints, ArmType/ArmingState enums, and the
                               internal _ResultCode enum for TotalConnect's
                               numeric response codes.
  exceptions.py                The exception hierarchy consumers catch
                                (TotalConnectError and its subclasses).
  __main__.py                  `python3 -m total_connect_client <username>` —
                                the command-line diagnostic tool referenced in
                                README Troubleshooting. Talks to a real account.
  live/                         Small standalone scripts (arm.py, disarm.py,
                                 bypass.py, trigger.py, sleepy.py, experimental.py)
                                 used by maintainers to exercise a REAL alarm
                                 panel by hand. They are excluded from coverage
                                 (`omit` in `[tool.coverage.run]`) and are never
                                 invoked by pytest, tox, or CI. Do not add a
                                 script here that anything automated could run —
                                 it would arm or disarm somebody's real house.
tests/                        The suite. Nothing here makes a real network call.
  const.py                     Recorded/sanitized API response fixtures — the
                                thing described above. This is where new
                                system data goes.
  conftest.py                   Autouse fixture that mocks auth endpoints for
                                 every test via requests_mock.
  common.py                     Shared helpers for building a logged-in
                                 TotalConnectClient against mocked responses.
  test_*.py                     One file per module under test.
docs/                          Reference and how-to material (see docs/ for the
                                current set: DEVELOPER.md, DEVICES.md, DOORBELL.md,
                                RESULT_CODES.md, ZONE_TYPES.md, REST_NOTES.md, VERSIONS.md).
.github/                       Issue/PR templates and the CI workflows
                                (python-package.yml runs tox on PRs;
                                python-publish.yml publishes to PyPI on release).
```

## Invariants a PR must not break

This library's only real consumer at scale is the Home Assistant
`totalconnect` integration, plus whatever standalone scripts people run
against `pip install total-connect-client`. That makes the bar for "safe
change" narrower than it looks:

- **Public API changes are breaking changes.** Anything exported from
  `total_connect_client/__init__.py` (`TotalConnectClient`, `ArmingHelper`,
  `ArmType`, `ArmingState`, `ZoneType`, `ZoneStatus`, `ResultCode`) or any
  public method/property on `TotalConnectLocation`, `TotalConnectPartition`,
  `TotalConnectZone`, or `TotalConnectUser` is something Home Assistant
  imports and calls directly. Renaming, removing, or changing the signature
  or return type of any of these needs to be called out explicitly in the PR
  description, not discovered later.
- **The exception hierarchy in `total_connect_client/exceptions.py` is part
  of that public API.** Consumers catch specific exception types
  (`AuthenticationError`, `UsercodeInvalid`, `FeatureNotSupportedError`,
  etc.). Don't rename an existing exception or change which cases raise it
  without flagging it as breaking.
- **No real credentials, usercodes, or account/device identifiers anywhere in
  the diff** — not in `tests/const.py` fixtures, not in docs examples, not in
  commit messages. Use obvious placeholders (`"1234"`, `LOCATION_ID = 123456`
  in the style already used in `tests/const.py`).
- **`mypy --strict` stays clean.** `[tool.mypy]` in `pyproject.toml` sets
  `strict = true` and `disallow_untyped_defs = true` for
  `total_connect_client/`. New code needs full type annotations.
- **`ruff check` and `ruff format --check` stay clean.** Run them before
  opening a PR; CI runs them on every push.
- **New behavior gets a test.** Every existing test builds its fixture data
  from `tests/const.py` and mocks HTTP with `requests_mock` — follow that
  pattern rather than adding a test that needs a real account.
- **New `_ResultCode` values need a `docs/RESULT_CODES.md` entry.** That
  table is the project's maintained documentation for TotalConnect's numeric
  codes; a code handled in `const.py` or `client.py` without a matching table
  row is a code nobody else can look up when they hit it.
- **Nothing under `total_connect_client/live/` runs in CI, ever.** Those
  scripts arm, disarm, bypass, or trigger a real panel. If your change
  touches that directory, double-check it's still unreachable from `pytest`,
  `tox`, and the GitHub Actions workflows.

If you're not sure whether a change you're making is "breaking" in the sense
above, ask in the PR rather than guessing — Home Assistant users are the ones
who find out the hard way if we guess wrong.
