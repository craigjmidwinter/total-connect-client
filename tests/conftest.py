"""Global test fixtures."""

import sys

import pytest
import requests_mock
from const import (
    HTTP_RESPONSE_CONFIG,
    HTTP_RESPONSE_SESSION_DETAILS,
    HTTP_RESPONSE_TOKEN,
)

from total_connect_client.const import (
    AUTH_CONFIG_ENDPOINT,
    AUTH_TOKEN_ENDPOINT,
    HTTP_API_SESSION_DETAILS_ENDPOINT,
)

LIVE_PACKAGE = "total_connect_client.live"


def pytest_sessionfinish(session, exitstatus):
    """Fail the run if any `total_connect_client.live` module was imported.

    Those scripts arm, disarm, bypass, and trigger real alarm panels, and none
    of them has an `if __name__ == "__main__":` guard — importing one executes
    its whole body, including `getpass` and a live client construction. Their
    `sys.argv` length checks are not a safety net either: under pytest,
    `sys.argv` is `[pytest_path] + user args`, so ordinary invocations satisfy
    one guard or another (`pytest -q` has length 2, which is exactly what
    `live/trigger.py` accepts).

    Nothing imports them today, so this hook is a tripwire rather than a fix:
    it turns "we happen not to import these" into something CI states out
    loud. AGENTS.md requires `live/` stay unreachable from pytest, tox, and
    GitHub Actions; until now nothing enforced that.
    """
    leaked = sorted(m for m in sys.modules if m == LIVE_PACKAGE or m.startswith(LIVE_PACKAGE + "."))
    if leaked:
        session.exitstatus = 1
        print(
            "\nERROR: test run imported modules under "
            f"{LIVE_PACKAGE}, which talk to a real alarm panel:\n"
            + "".join(f"  - {m}\n" for m in leaked)
            + "These scripts execute on import and have no __main__ guard.\n"
            "Nothing in tests/ may import them. See AGENTS.md.",
            file=sys.stderr,
        )


@pytest.fixture(autouse=True)
def mock_http_requests():
    """Automatically mock any direct HTTP requests, right now these are used for authentication only."""
    with requests_mock.Mocker() as rm:
        rm.get(AUTH_CONFIG_ENDPOINT, json=HTTP_RESPONSE_CONFIG, status_code=200)
        rm.post(AUTH_TOKEN_ENDPOINT, json=HTTP_RESPONSE_TOKEN, status_code=200)
        rm.get(
            HTTP_API_SESSION_DETAILS_ENDPOINT,
            json=HTTP_RESPONSE_SESSION_DETAILS,
            status_code=200,
        )
        yield
