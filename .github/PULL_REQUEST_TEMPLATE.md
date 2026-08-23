## What does this change do?

<!-- One or two sentences. If it fixes an issue, link it: "Fixes #123". -->

## Checklist

- [ ] No real credentials, usercodes, or account/device IDs anywhere in the
      diff (including test fixtures and commit messages) — placeholders only.
- [ ] If this changes anything exported from `total_connect_client/__init__.py`,
      or any public method/property/exception on `TotalConnectClient`,
      `TotalConnectLocation`, `TotalConnectPartition`, `TotalConnectZone`,
      `TotalConnectUser`, or the `exceptions.py` hierarchy — I've called that
      out explicitly below, because Home Assistant's `totalconnect`
      integration depends on this package.
- [ ] New `_ResultCode` values are documented in `docs/RESULT_CODES.md`.
- [ ] New behavior has a test in `tests/`, using `tests/const.py` fixtures
      and `requests_mock` (no test requires a real TotalConnect account).
- [ ] `uv run --group lint ruff check total_connect_client tests` and
      `ruff format --check` are clean.
- [ ] `uv run --group type mypy -p total_connect_client` is clean (`--strict`).
- [ ] `uv run --group dev pytest -q` passes locally.
- [ ] Nothing under `total_connect_client/live/` was wired into `pytest`,
      `tox`, or a GitHub Actions workflow — those scripts talk to a real
      alarm panel and must stay manual-only.

## Breaking changes (if any)

<!-- Describe what a downstream consumer (Home Assistant, or someone's
     standalone script) needs to change. Leave "None." if there are none. -->

None.
