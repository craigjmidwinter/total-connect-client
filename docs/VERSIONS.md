# Version Information

**Mode:** Reference (status page). This page used to try to track which
Home Assistant version bundled which `total-connect-client` version, to help
debug user issues. It stopped being maintained after the `2022.1` /
`2022.2.0` entry — the current package version is `2026.7`, four years and
roughly 45 releases later. Rather than guess at the missing HA pairings (they
require checking Home Assistant's own dependency manifests release by
release, which nobody has done reliably), this page now does two
things honestly: records this package's own release history (verifiable from
GitHub Releases), and tells you where to look up the HA pairing yourself.

## How to find which total-connect-client version your Home Assistant uses

Home Assistant pins this package's version in the `totalconnect` integration's
`manifest.json` (`requirements` field), in the
[home-assistant/core](https://github.com/home-assistant/core) repo. To check:

```bash
# from a home-assistant/core checkout, or via the GitHub UI:
grep -A2 '"domain": "totalconnect"' -r homeassistant/components/totalconnect/manifest.json
```

or browse
<https://github.com/home-assistant/core/blob/dev/homeassistant/components/totalconnect/manifest.json>
directly (use the `dev` branch for the upcoming release, or a version tag
like `2026.8.0` for a specific released version).

## This package's release history (verified)

Pulled from `gh release list --limit 60` against this repo on 2026-08-21 — every date below is the actual GitHub release
timestamp, not an estimate.

| total-connect-client | Released |
|---|---|
| 2026.7 | 2026-07-06 |
| 2025.12.2 | 2025-12-31 |
| 2025.12.1 | 2025-12-31 |
| 2025.12 | 2025-12-31 |
| 2025.8 | 2025-09-01 |
| 2025.5 | 2025-05-04 |
| 2025.1.4 | 2025-01-28 |
| 2025.1.3 | 2025-01-28 |
| 2025.1.2 | 2025-01-27 |
| 2025.1 | 2025-01-21 |
| 2024.12.1 | 2024-12-24 |
| 2024.12 | 2024-12-07 |
| 2024.5 | 2024-05-05 |
| 2024.4 | 2024-04-28 |
| 2023.12.1 | 2023-12-02 |
| 2023.12.0 | 2023-12-02 |
| 2023.11.1 | 2023-11-18 |
| 2023.11 | 2023-11-17 |
| 2023.7 | 2023-07-04 |
| 2023.2 | 2023-02-24 |
| 2023.1 | 2023-01-14 |
| 2022.10 | 2022-10-14 |
| 2022.5 | 2022-05-07 |
| 2022.3 | 2022-03-20 |
| 2022.2.1 | 2022-02-19 |
| 2022.2 | 2022-02-12 |

For the complete list back to `v0.53` (2020), and for pre-release (`.rcN`)
builds, run `gh release list --limit 60` against this repo, or see
<https://github.com/craigjmidwinter/total-connect-client/releases>. For
what changed in each release, see [`../CHANGELOG.md`](../CHANGELOG.md).

## Last known Home Assistant pairing (unverified beyond this point)

This table was accurate when it was last hand-maintained in 2022. It is
**not** independently re-verified — treat it as historical record, not
current guidance:

| total-connect-client | Home Assistant | Notes |
|---|---|---|
| 2022.1 | 2022.2.0 | |
| 2021.11.4 | 2021.12.0 | |
| 2021.8.3 | 2021.11.0 | |
| 0.57 | 2021.3 | |
| 0.55 | 0.111.0 | |
| 0.54.1 | 0.108.2 | |

If you need a current pairing, use the manifest lookup above instead of this
table.
