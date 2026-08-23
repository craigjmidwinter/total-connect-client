# total-connect-client docs

## Why this docs set doesn't look like a typical Diátaxis docs set

These docs mostly follow [Diátaxis](https://diataxis.fr/) — tutorial, how-to,
reference, and explanation kept separate. Two places where they deliberately
don't, stated plainly:

1. **Most of this directory is field notes supplementing an incomplete vendor
   reference, not product documentation.** Resideo publishes an
   [incomplete generated reference](https://rs.alarmnet.com/TC2API.TCResource/),
   but it omits many endpoint details and result-code semantics and provides
   no verified third-party SDK or compatibility contract. Everything in
   `RESULT_CODES.md`, `ZONE_TYPES.md`, `DEVICES.md`, and `DOORBELL.md` was
   recovered by testing against real panels and reading traffic — not from a
   complete spec. That makes them reference pages in *shape*
   (tables you look things up in) but their provenance is empirical, not
   authoritative, and each page now says so at the top. We are not pretending
   Resideo published this; we are telling you where it actually came from and
   how much to trust it.
2. **`DEVELOPER.md` folds tutorial and how-to together.** This is a small
   library with one real "getting started" path for non-Home-Assistant
   consumers. Splitting a five-minute walkthrough into a separate tutorial
   file and a separate how-to file would force a reader hunting for "how do I
   arm the system" to jump between two thin pages for no benefit.

Everything else in this set — the API reference, the architecture
explanation, result codes, zone types, device notes, and troubleshooting —
follows Diátaxis normally: reference pages are exhaustive lookup tables,
explanation pages describe *why* the client is shaped the way it is, and
nothing narrative is interleaved with an option table.

No docs site is published for this project — there are no GitHub Pages for
this repo. These pages render as plain Markdown on GitHub.

## Map

| Page | Mode | Who it's for |
|---|---|---|
| [`DEVELOPER.md`](DEVELOPER.md) | Tutorial + how-to (see justification above) | A developer integrating this library outside Home Assistant, from `pip install` to a working arm/disarm loop |
| [`troubleshooting.md`](troubleshooting.md) | How-to | Anyone (HA user or library consumer) debugging a failing alarm connection who needs to capture and share diagnostic info |
| [`api-reference.md`](api-reference.md) | Reference | Any consumer programming against the public classes, methods, enums, and exceptions |
| [`RESULT_CODES.md`](RESULT_CODES.md) | Reference (empirical) | A developer who got a `ResultCode` back and needs to know what it means |
| [`ZONE_TYPES.md`](ZONE_TYPES.md) | Reference (empirical) | A developer mapping `ZoneTypeId` values to real sensor behavior |
| [`DEVICES.md`](DEVICES.md) | Reference (empirical) | A developer mapping `DeviceClassID`/`PanelType`/`PanelVariant` to real hardware |
| [`DOORBELL.md`](DOORBELL.md) | Reference (empirical, thin/TBD) | A developer investigating Skybell/doorbell device calls |
| [`architecture.md`](architecture.md) | Explanation | Anyone who wants to understand the auth flow, the retry/reauth model, and why the client is shaped this way before changing or debugging it |
| [`REST_NOTES.md`](REST_NOTES.md) | Explanation (raw field notes) | A developer debugging an unusual response who wants to see prior reverse-engineered API discoveries, largely verbatim |
| [`VERSIONS.md`](VERSIONS.md) | Reference (status page) | Anyone trying to correlate a `total-connect-client` release with a Home Assistant release |

For the full history of what changed release to release, see
[`../CHANGELOG.md`](../CHANGELOG.md) in the repo root (maintained by a
separate pass; if it doesn't exist yet when you read this, check the GitHub
Releases page instead).

## Filenames were kept as-is on purpose

Every pre-existing file keeps its original name and path
(`DEVELOPER.md`, `DEVICES.md`, `DOORBELL.md`, `REST_NOTES.md`,
`RESULT_CODES.md`, `VERSIONS.md`, `ZONE_TYPES.md`). Two things point at these
paths and neither should break: `README.md` links `docs/DEVELOPER.md`, and a
docstring comment in `total_connect_client/device.py` references
`docs/DEVICES.md`. GitHub issues going back years may also link directly into
`RESULT_CODES.md` or `ZONE_TYPES.md` at specific lines. Renaming any of these
would cost real inbound links for a cosmetic gain (matching a naming
convention), so only the genuinely new pages (`index.md`, `api-reference.md`,
`architecture.md`, `troubleshooting.md`) get the fresh names.
