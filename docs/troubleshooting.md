# Troubleshooting

**Mode:** How-to. This page walks through diagnosing a TotalConnect
connection problem and, if you need help from the maintainers, capturing
system information to attach to a GitHub issue. It replaces the
"Troubleshooting" section that used to live in the root `README.md`; the
README now links here.

For what this library and its command-line tool actually hold in memory and
in logs, and the full checklist of what to scrub before you post anything
publicly, see [`../SECURITY.md`](../SECURITY.md) — this page links to it
rather than duplicating it, so there's one place that list can be kept
current.

## Zone status requires "Sensor Activities"

To see zones that are faulted (open), your Total Connect account must have
"Sensor Activities" enabled. Your alarm monitoring company may charge an
extra fee to enable this. If available, you can turn it on in the Total
Connect 2 web portal at **Notifications → Sensor Activities**, or in the
Total Connect mobile app at **More → Settings → Notifications → Sensor
Activities**.

## General troubleshooting order

If you're having trouble with your system, or see an error message, work
through these in order:

1. **Check the TotalConnect system status page:**
   <https://status.resideo.com/> — rules out a vendor-side outage before you
   spend time debugging your own setup.
2. **Check your internet connection.** TotalConnect depends on two separate
   network paths: your alarm panel to the TotalConnect server, and your
   client (e.g. your Home Assistant host) to the TotalConnect server. Either
   one being down looks the same from here — confirm both your alarm and
   your client are actually online. If the failure looks like a long silent
   hang rather than an immediate error, see "A hang before the error is
   expected" below — that's very likely what's happening, not a frozen
   process.
3. **Gather diagnostics** (see below) before opening an issue — it's the
   single most useful thing you can attach, because the TotalConnect API
   documents almost none of its status codes, and different accounts/panels
   have been observed returning different codes for what looks like the same
   condition.

## Capturing diagnostics from Home Assistant

1. Go to `https://<your_home_assistant>/config/integrations`.
2. Find the TotalConnect integration card and click the three-dot menu in
   its bottom-right corner.
3. Click **Download Diagnostics**.

If you can't download diagnostics that way, use the command-line method
below instead — it works from any machine, not just the one running Home
Assistant.

## Capturing diagnostics from the command line

Run this from any computer with a reasonably current Python installed. It
does not need to be the machine hosting your Home Assistant instance.

### 1. Check your Python version first

This library requires **Python 3.10 or later**. Below that, `pip` does not
error or warn you — it silently installs the newest release still compatible
with your interpreter, which can be years old and built on a completely
different (and no longer maintained) transport layer. On a real Python 3.9.6
test, `pip install total-connect-client` succeeded with no warning at all,
but installed release `2024.4` — over two years behind current — which still
uses the old deprecated SOAP client (`zeep`) instead of the REST/OAuth client
this and all recent versions use. If something in this guide doesn't match
what you're seeing (different error shapes, different exceptions, no
`test.log` file), the first thing to check is `pip show total-connect-client`
for the installed `Version:` line, and confirm `python3 --version` is 3.10+.

### 2. Create a virtual environment, then install

Don't run `pip install total-connect-client` directly against your system
Python. Most current Linux distributions and current Homebrew Python refuse
that outright (PEP 668, "externally managed environment"); even where it's
allowed, a venv keeps this install isolated from everything else on the
machine. Confirmed on a stock, PEP-668-managed Python (Homebrew Python on
macOS is one; current Debian/Ubuntu/Fedora are others) — the plain command
fails immediately:

```
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

Exit code 1. Do this instead — it works everywhere, PEP 668 or not:

```bash
python3 -m venv .venv
source .venv/bin/activate      # on Windows: .venv\Scripts\activate
python3 -m pip install total-connect-client
python3 -m total_connect_client username
```

### 3. Run the diagnostic command

```bash
python3 -m total_connect_client username
```

You'll be prompted for your password interactively (it isn't echoed to the
terminal) — this only works with a real terminal attached. If you run this
same command with no terminal attached — piped from a script, a cron job, or
CI, with no password supplied another way — it does not print a clean
"provide a password" message; it crashes with a low-level `termios.error` (or
`EOFError`, depending on exactly how stdin is closed) before it ever reaches
the network. If you need this non-interactively, pass the password as the
optional second argument instead: `python3 -m total_connect_client username
password`.

Run with no arguments at all, or with more than two, and the tool fails
cleanly instead — this check happens before anything else:

```
$ python3 -m total_connect_client
usage:  python3 -m total_connect_client username [password]
```

(exit code 1; three arguments produce the identical message and exit code).

If your username/password are wrong, you'll get a full Python traceback (not
a friendly message — that's a known rough edge in the CLI, not something
this page can paper over) ending in a line like:

```
total_connect_client.exceptions.AuthenticationError: ('AUTHENTICATION_FAILED', {'error': '-100', 'error_description': 'Authentication Failed'})
```

That specific exception means what it says — bad username or password (or a
locked account) — not a bug in the tool. Double-check your TotalConnect 2
login (the account password, not an alarm usercode) and try again.

#### A hang before the error is expected

If your network can't reach TotalConnect at all (offline, firewalled,
captive portal, etc.), the command does not fail fast. Measured against a
deliberately unreachable network path: it took **24 seconds** of silent
retrying before finally raising:

```
total_connect_client.exceptions.ServiceUnavailable: Error connecting to Total Connect service: HTTPSConnectionPool(host='totalconnect2.com', port=443): Max retries exceeded with url: /application.config.json (Caused by ProxyError(...))
```

There is no progress indicator during those 24 seconds. If the command
appears to hang for roughly half a minute before printing anything, that is
expected behavior (the library retrying internally), not a frozen terminal —
give it time to reach `ServiceUnavailable` rather than assuming it's stuck.

### 4. Save the output for sharing

To redirect the printed output straight to a file:

```bash
python3 -m total_connect_client username > my_info.txt
```

The interactive password prompt still goes straight to the terminal either
way (it's read via `getpass`, not printed to stdout), so it never ends up in
`my_info.txt`.

### This command also writes a log file you were not told about

Running `python3 -m total_connect_client` calls
`logging.basicConfig(filename="test.log", level=logging.DEBUG)` — and it does
this **before parsing its own arguments**, so `test.log` is created even by a
bare usage-error run with no username at all. Every run silently creates (or
appends to) a file named `test.log` in your current directory, independent
of, and in addition to, whatever prints to your terminal or gets redirected
to `my_info.txt`. On a real run, `test.log` reached 4,461 bytes and captured
substantially more than the terminal output does — see
[`../SECURITY.md`](../SECURITY.md#what-this-library-holds-and-what-to-scrub-before-you-post)
for exactly what it can contain.

Nothing in the command's own output mentions this file. If you don't already
know to look for it, you can end up sharing it by accident — e.g. by zipping
up a working directory and attaching the zip to an issue. **`test.log` sits
in the same directory as `my_info.txt` and is not covered by the "put it in
a file for sharing" instructions above — check for it separately.**

## What the output actually exposes — read before sharing

The previous version of this warning said the command's output "includes
private information including your username and password." That named the
wrong secret: the client's own `__str__` (what prints to your terminal, and
what `my_info.txt` captures) prints `Password: [hidden]` — your account
password is not printed in the clear there. What the terminal output and
`my_info.txt` **do** print in the clear: your TotalConnect **username**, and
location/device/zone/partition identifiers, names, and other account
details.

**Usercodes specifically:** if you're troubleshooting via
`python3 -m total_connect_client username` as documented above, the printed
output will *not* contain a usercode — that command never asks for or uses
one (`Usercode: {}`, always empty), so there's nothing to leak there. The
usercode-in-the-clear risk is real, but it applies elsewhere: if you or an
integration (this library's own `total_connect_client/live/` scripts, or
your own code) construct a `TotalConnectClient` **with** a `usercodes`
argument and ever print that client or its locations, the usercode prints
unredacted — see
[`api-reference.md`](api-reference.md#the-usercodes-dict--sharp-edges) and
[`../SECURITY.md`](../SECURITY.md) for the full detail. Separately, if you
mistype a usercode while validating one (`TotalConnectLocation.validate_usercode()`),
the rejected code is logged at `ERROR` level — visible in default logging
setups, no debug flag required — so an ordinary log capture can contain a
usercode even without DEBUG logging enabled. Again, see
[`../SECURITY.md`](../SECURITY.md) for the details on that.

`test.log` is the one that goes well beyond what's described above — full
DEBUG-level request/response logging, which is a materially bigger exposure
than the terminal output. **Before sharing anything — the terminal output,
`my_info.txt`, or `test.log` — with anyone, developers included, read
[`../SECURITY.md`](../SECURITY.md) and scrub everything it lists.** Don't
rely on this page's shorter summary above as the complete list; `SECURITY.md`
is the maintained, authoritative one.

## Filing an issue

Once you've captured and scrubbed your diagnostics per
[`../SECURITY.md`](../SECURITY.md), open an issue on GitHub with your problem
description and the redacted system information attached:
<https://github.com/craigjmidwinter/total-connect-client/issues>.

Why we ask for this: the TotalConnect API documentation provides little
information about the status codes and other data it returns about your
system. This library's result-code catalogue
([`RESULT_CODES.md`](RESULT_CODES.md)) and device/zone-type notes
([`DEVICES.md`](DEVICES.md), [`ZONE_TYPES.md`](ZONE_TYPES.md)) were built from
real accounts and real panels, and different users' systems have repeatedly
turned out to report different codes for what looks like the same condition.
