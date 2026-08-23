# Security Policy

## Reporting a vulnerability

Please report a suspected vulnerability privately through the repository's
[Security advisory form](https://github.com/craigjmidwinter/total-connect-client/security/advisories/new).
GitHub private vulnerability reporting is the preferred channel.

If you cannot use the advisory form, email the package maintainer at the
address listed as the `authors` contact in `pyproject.toml`:

**craig.j.midwinter@gmail.com**

Include:
- What you found and why you think it's a security issue (not just a bug).
- Steps to reproduce, if you have them, with any credentials, usercodes, or
  account/device IDs already stripped out (see below).
- Whether you think it also affects the Home Assistant `totalconnect`
  integration, which depends on this package.

Please don't open a public GitHub issue for a suspected vulnerability until
the maintainers have had a chance to look at it.

## Scope

In scope: the `total_connect_client` package as published on PyPI and this
source repository — authentication handling, HTTP transport, and anything
that could leak or mishandle a user's TotalConnect credentials or alarm
usercodes.

Out of scope: TotalConnect's own servers and API (report those to Resideo,
not here — check [status.resideo.com](https://status.resideo.com/) first to
see if an incident is already known), and the Home Assistant `totalconnect`
integration itself, which lives in
[home-assistant/core](https://github.com/home-assistant/core) and has its
own security process.

## What this library holds, and what to scrub before you post

This is worth reading before you file *any* issue, not just a security one,
because maintainers routinely ask users to attach logs or diagnostic output
when troubleshooting.

- **A `TotalConnectClient` instance holds your TotalConnect account
  password and your alarm usercode(s) in memory** for the life of the
  process (`self.password`, `self.usercodes` in `total_connect_client/client.py`).
  `TotalConnectClient.__str__()` masks the password (`Password: [hidden]`)
  but **prints usercodes in the clear** — if you (or something you call,
  such as `print(client)`) ever renders that object as a string, your
  usercode is now in that output.
- **A rejected usercode is logged at `ERROR` level, not `DEBUG`.**
  `location.py`'s `validate_usercode()` logs `Could not validate usercode
  ({usercode})` through `LOGGER.error(...)` when the panel rejects a code.
  `ERROR` is visible in default logging setups — including Home Assistant's,
  with no debug option enabled — so mistyping a usercode during setup can put
  that attempt in an ordinary log a user would think is safe to paste.
- **`DEBUG`-level logging includes full request and response bodies.**
  `client.py`'s `http_request()` logs the endpoint, method, and the complete
  `params`/`data` dictionaries at `LOGGER.debug(...)` for every call made to
  TotalConnect — and arm/disarm/bypass calls carry your usercode in that
  request body. The JSON response bodies are logged in full as well.
- **The bundled command-line tool writes DEBUG logs to a file by default.**
  `python3 -m total_connect_client <username>` (and the scripts under
  `total_connect_client/live/`) call
  `logging.basicConfig(filename="test.log", level=logging.DEBUG)` — running
  it creates `test.log` in your current directory containing everything
  above — all seven entry points (`__main__.py` and each of the six scripts
  under `live/`) set it identically, and `__main__.py` does so before it even
  parses its arguments, so the file appears even on a usage error. The
  README's troubleshooting section asks users to run this command and share
  the output; **the resulting file can contain your usercode, your OAuth
  access and refresh tokens, session cookies, and the full contents of every
  request TotalConnect made on your behalf.** A real run of the documented
  command produced a 4,461-byte `test.log` containing exactly that.

**Before attaching any log, `test.log`, or command output to a GitHub issue or
private security report, or emailing it to a maintainer, scrub:**

- Your TotalConnect username and password.
- Every alarm usercode.
- Location IDs, device IDs, and security device IDs (they identify your
  specific panel/account, not a security secret by themselves, but there's
  no reason to publish them).
- Any OAuth token or session ID values that appear in logged responses.

If you're not sure whether a value is sensitive, redact it — a maintainer
can always ask for it back if it turns out to matter, and it's much easier
than un-publishing a leaked usercode.

## Supported versions

This project doesn't maintain parallel release branches; only the latest
version on [PyPI](https://pypi.org/project/total-connect-client/) receives
fixes. If you're reporting a vulnerability, please confirm it still
reproduces on the latest release first.
