# total-connect-client repository guide

## Runtime and package surface

- This is the `total_connect_client` Python package published to PyPI as
  `total-connect-client`. It requires Python 3.10 or newer; CI covers 3.10
  through 3.14.
- `TotalConnectClient` authenticates during construction and normally talks to
  the Total Connect 2 REST service. Resideo publishes an
  [incomplete generated reference](https://rs.alarmnet.com/TC2API.TCResource/),
  but it omits many endpoint details and result-code semantics and provides no
  verified third-party SDK or compatibility contract. The client therefore
  relies on reverse-engineered behavior. Do not use real accounts, panels,
  credentials, or usercodes for automated verification.
- Home Assistant's `totalconnect` integration is the primary downstream
  consumer. Treat exports from `total_connect_client/__init__.py`, public
  classes and methods, return types, and the exception hierarchy in
  `total_connect_client/exceptions.py` as compatibility-sensitive API.

## Setup and required checks

Use the dependency groups declared in `pyproject.toml`:

```bash
uv venv
uv pip install -e . --group dev
uv run --group dev pytest -q
uv run --group lint ruff check total_connect_client tests
uv run --group lint ruff format --check total_connect_client tests
uv run --group type mypy -p total_connect_client
uv run --group coverage coverage run -m pytest
uv run --group coverage coverage report
```

The committed CI contract is tox, configured in `pyproject.toml` and invoked
by `.github/workflows/python-package.yml`:

```bash
tox -e py310,py311,py312,py313,py314
tox -e lint
tox -e type
tox -e coverage
```

Run the direct `uv` test, lint, format, and type commands before committing.
Use the applicable tox environments when changing packaging, dependency
groups, Python-version support, or CI. `uv.lock` is intentionally ignored;
do not add it unless the project's dependency-resolution policy changes.

## Test and source boundaries

- `tests/const.py` holds sanitized recorded API responses. Tests use
  `requests_mock`; no test may depend on a live Total Connect account or make
  a real Total Connect request.
- Add or update a recorded fixture and a focused test for new panel- or
  response-specific behavior. Use the existing placeholder IDs and usercode
  style; never paste captured identifiers or secrets.
- `total_connect_client/live/` contains manual scripts that can arm, disarm,
  bypass, or trigger a real alarm. Keep that directory unreachable from
  pytest, tox, and GitHub Actions.
- `total_connect_client/__main__.py` is a live diagnostic entry point, not an
  offline smoke test. Running it creates or appends `test.log` in the current
  directory, even for a usage error.
- A new or changed `_ResultCode` in `total_connect_client/const.py` must have a
  matching entry in `docs/RESULT_CODES.md` and tests for its mapped behavior.
- Keep `mypy --strict` clean for the package and Ruff clean for the package and
  tests. New behavior requires a fixture-backed test.

## Security invariants

- Do not commit or share real usernames, passwords, alarm usercodes, OAuth
  tokens, session IDs, location IDs, device IDs, or security-device IDs. Keep
  them out of source, fixtures, docs, diffs, and commit messages; redact any
  generated diagnostic output before sharing it.
- Treat diagnostic output and `test.log` as sensitive. Debug logging includes
  full request and response bodies; rejected usercodes can appear at error
  level; `TotalConnectClient.__str__()` masks the password but can expose the
  username, identifiers, and configured usercodes.
- Do not weaken TLS, authentication, retry, or credential handling without an
  explicit security review. Follow `SECURITY.md` for vulnerability handling.

## Release and documentation coupling

- `master` pushes and pull requests run `.github/workflows/python-package.yml`.
  They do not publish a package.
- Publishing is triggered only by a published GitHub Release. The release
  workflow builds an sdist and wheel with `python -m build`, then publishes
  them to PyPI through trusted publishing.
- The package version lives in `pyproject.toml` and uses the project's
  CalVer-like scheme. Keep it, `CHANGELOG.md`, release naming, and user-facing
  version claims aligned.
- Do not alter public API or behavior in a documentation/tooling-only change.
  Call out any intentional breaking change for Home Assistant consumers.
- Keep user-facing API documentation synchronized with implementation,
  especially `docs/api-reference.md`, `docs/architecture.md`, and the
  catalogues under `docs/`.
