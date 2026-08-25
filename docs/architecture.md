# Architecture

**Mode:** Explanation. This page describes *why* `TotalConnectClient` is
shaped the way it is — the auth flow, the retry/reauth model, and a couple of
open interface questions — so you understand the mechanism before you change
or debug it. For exact signatures, see [`api-reference.md`](api-reference.md).

## Why this shape at all

Resideo publishes an
[incomplete generated reference](https://rs.alarmnet.com/TC2API.TCResource/)
for Total Connect 2, but it omits many endpoint details and result-code
semantics and provides no verified third-party SDK or compatibility contract.
This library talks to the same REST backend the official mobile/web apps use
(`rs.alarmnet.com`), filling those gaps by reverse-engineering real traffic
(see `REST_NOTES.md`). That backend requires a specific multi-step login sequence
before it will answer anything else, and its errors are reported as HTTP-200
responses with a `ResultCode` field rather than as HTTP status codes for most
failure modes — both of which drive the shape of `TotalConnectClient`.

## Auth flow

Constructing a `TotalConnectClient` runs this sequence synchronously, before
`__init__` returns:

```
 1. GET  https://totalconnect2.com/application.config.json   (_get_configuration)
      → RSA public key (PEM), client_id, app_id, app_version
 2. RSA-encrypt username and password with that key           (_encrypt_credential)
      → PKCS1 v1.5 padding (not OAEP — the padding scheme is
        dictated by the server, this library just matches it)
 3. POST https://rs.alarmnet.com/TC2API.Auth/token             (_request_token)
      → OAuth2 "password" grant (RFC 6749 §4.3, via
        oauthlib's LegacyApplicationClient), body carries the
        RSA-encrypted username/password as the grant's
        username/password fields
      → OAuth2Session holds the resulting access/refresh token
 4. GET  .../api/v3/authentication/sessiondetails                (_get_session_details)
      → ModuleFlags, UserInfo, and the account's Locations list
      → builds self._locations: dict[int, TotalConnectLocation]
 5. per location (if load_details=True, the default):
      get_partition_details() + get_zone_details() + get_panel_meta_data()
```

Two things about this that surprise people coming from typical REST APIs:

- **Credentials are RSA-encrypted client-side before being sent as OAuth2
  password-grant fields**, not sent over TLS alone. The RSA key itself is
  fetched fresh from the config endpoint on every login — it isn't
  hardcoded — so this library never ships or pins a key.
- **Step 5 can be slow.** For an account with several locations, each with
  many zones, constructing a `TotalConnectClient` can mean a dozen-plus HTTP
  round-trips before your code gets control back. Pass `load_details=False`
  if you want the constructor to return quickly and fetch details yourself,
  lazily, per location.

## Retry and reauthentication model

Every outbound call funnels through `TotalConnectClient.http_request()`,
which delegates to `_request_with_retries()`. That function wraps one HTTP
call and:

1. Runs the request.
2. If the *parsed JSON body's* `ResultCode` is one of `INVALID_SESSION`,
   `INVALID_SESSIONID`, `CONNECTION_ERROR`, `FAILED_TO_CONNECT`,
   `CANNOT_CONNECT`, or `BAD_OBJECT_REFERENCE` — or the HTTP status is `401`
   or in `[429, 500, 502, 503, 504]` — it's treated as retryable.
3. A session-related failure (`InvalidSessionError`, or an `OAuth2Error`/
   `ValueError` from the OAuth layer) triggers a full **re-authentication**
   (`self.authenticate()` — i.e. steps 1–3 above, again) before the next
   attempt. A connection-related failure (`RetryableTotalConnectError`,
   `requests.RequestException`) just sleeps `retry_delay` seconds and retries
   the same request.
4. This repeats up to `MAX_RETRY_ATTEMPTS = 5` times (a class constant, not
   parameterized). **What surfaces when attempts are exhausted depends on
   which failure exhausted them** — there is no single exception to catch:

   | what failed | what escapes after the last attempt |
   | --- | --- |
   | a retryable `ResultCode` from step 2, or a retryable HTTP status | the original `RetryableTotalConnectError` (or subclass), re-raised unchanged |
   | a transport error (`requests.RequestException`) | `ServiceUnavailable` |
   | a session/OAuth error (`InvalidSessionError`, `OAuth2Error`, `ValueError`) | `ServiceUnavailable` |

   So catching only `ServiceUnavailable` will **not** cover exhausted
   retries of `CONNECTION_ERROR`, `FAILED_TO_CONNECT`, `CANNOT_CONNECT`,
   `BAD_OBJECT_REFERENCE`, or a persistent 429/500/502/503/504 — those reach
   you as `RetryableTotalConnectError`. Catch both, or catch
   `TotalConnectError`, which is the common base. (Re-raising the specific
   type is deliberate: it preserves what actually went wrong. Earlier
   revisions of this page claimed exhaustion always produced
   `ServiceUnavailable`, which was wrong for the first row.)

`requests.adapters.Retry` is also configured on the underlying
`requests.Session` (`max_retries=5`, `status_forcelist=[429, 500, 502, 503,
504]`) — so some transient HTTP failures are retried at the `urllib3`
transport layer *before* `_request_with_retries` even sees them, on top of
the application-level retry described above.

**The important asymmetry:** all of that automatic retry/reauth happens
*inside* `http_request()`, on the raw HTTP call and the `ResultCode` values
listed in step 2 above. The broader result-code-to-exception mapping in
`raise_for_resultcode()` — which most `location.py`/`partition.py` methods
call *after* `http_request()` already returned — runs outside that retry
loop. So `PartialResponseError`, despite subclassing
`RetryableTotalConnectError` and despite its docstring calling these errors
"rather frequent," is **not** retried automatically. Home Assistant's
integration retries at a higher level for exactly this reason. If you're
writing your own consumer, plan to do the same for anything raised from
`raise_for_resultcode()` that isn't handled inside `http_request()`. Full
per-exception detail is in
[`api-reference.md`'s exceptions table](api-reference.md#exceptions).

## Interface evolution

For the release-by-release history of what changed, see
[`../CHANGELOG.md`](../CHANGELOG.md). Two structural notes worth keeping in
mind if you're maintaining this library or integrating deeply with it:

- **Partitions were added after locations and zones existed.** That's why
  `TotalConnectLocation.arm()`/`disarm()` take an optional `partition_id`
  (`0` meaning "all partitions") rather than partition-scoped arming being the
  only path — the location-level call came first and had to stay working.
- **The `usercodes` dict's `"-1"` sentinel fallback is a known rough edge.**
  Today, if no usercode matches a location (see
  [`api-reference.md`](api-reference.md#the-usercodes-dict--sharp-edges)), the
  client silently falls back to the sentinel value `"-1"` and only a debug
  log line notes it — arm/disarm/bypass calls then fail later with
  `UsercodeInvalid`/`UsercodeUnavailable` instead of failing clearly at
  construction time. A future release may instead raise at construction time
  when the `usercodes` dict doesn't cover a location. This has not happened
  yet as of `2026.7`; if you're relying on the silent fallback, treat that as
  fragile.
