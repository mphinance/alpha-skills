---
name: broker-upstream-check
description: Check whether any broker in awesome-broker-mcp changed upstream. Probes each broker's /llms.txt, /llms-full.txt, /openapi.json, cited docs pages, MCP endpoints and GitHub repos, then diffs against a committed snapshot. Use when asked "did Robinhood/Schwab/any broker update", "what changed at the brokers", "check for broker updates", after a git pull of the directory, or before bumping any last_verified date.
---

# Broker upstream check

`scripts/check-freshness.mjs` asks how old *our* date is. This asks whether *they* changed.

## Run it

```bash
node scripts/check-upstream.mjs                # diff vs scripts/upstream-snapshot.json
node scripts/check-upstream.mjs robinhood etrade   # only these slugs
node scripts/check-upstream.mjs --update       # diff, then accept the new state as the snapshot
node scripts/check-upstream.mjs --strict       # exit 1 on any change (CI)
```

Takes ~90s for all entries (8 parallel probes, 12s timeout, one retry on transient failure, browser UA).
The last line, `coverage:`, says how many llms/openapi surfaces are readable, blocked, or absent.

A 403 is ambiguous: bot wall, or "no such file" (S3/CloudFront and API gateways 403 every missing
path; robinhood.com, upstox.com and api.connecttrade.com do). So each 403 origin is asked about a
path that cannot exist; if that canary also gets 403, the surface is **absent**, not blocked.
"Blocked" means a real wall (e.g. thinkmarkets.com serves a Cloudflare challenge).

**Walled sites** cannot be watched by the script. Read the page by hand in a real desktop
browser (Claude in Chrome passes Cloudflare where curl and headless Chromium do not), note it
in the entry's caveats, and only then bump `last_verified`. Wayback availability is a weak
fallback: it lags and rate-limits.

## Reading the output

| Tag | Meaning | Action |
|---|---|---|
| `CHANGED` | llms.txt / openapi.json / cited page / repo release or push moved | Open it, diff against the entry, update the entry if a claim is now wrong, then bump `last_verified` |
| `NEW` | A surface appeared that wasn't there (a broker just shipped llms.txt or an OpenAPI spec) | Read it; a new spec often means a new API or MCP route |
| `GONE` | A surface vanished or a repo got archived | Entry likely needs a status downgrade |
| `DEAD` | MCP endpoint 404/unreachable, or a cited page 404s | Verify by hand; fix the link or the status |
| `BLIND` | A surface that used to read fine is now 403/timeout/5xx. Not a change, not a removal | Re-run later; ignore unless it persists |
| `BASELINE` | First run only, lists what exists | Nothing |

## Rules

1. `--update` only **after** you have read the changes. The snapshot is the memory; blindly updating it buries the signal.
2. A hash change is a lead, not a verdict. Marketing pages churn; llms.txt and openapi.json changes are the high-signal ones.
3. Never bump `last_verified` from this script alone. That date means a human opened the source (see contributing.md).
4. MCP endpoints are probed with a JSON-RPC `initialize` POST (a live server answers 200 or 401/403; GET lies). Page hashes ignore digits, hex tokens and timestamps, and same-size page rewrites are skipped as ad churn.
5. Third-party hosts cited in an entry (aggregator blogs, news sites) get probed too; their `CHANGED` lines are usually noise.

## Wiring

- `scripts/install-hooks.sh` installs `post-merge`/`post-rewrite` hooks so the check runs after every `git pull` (report-only; `SKIP_UPSTREAM_CHECK=1 git pull` skips it).
- `.github/workflows/upstream.yml` runs it Mondays 14:00 UTC and opens/updates one `upstream-changes` issue, closing it on a clean run. It never edits entries or the snapshot: a human reads, fixes the entry, then runs `--update`.
- Unknown slug exits 2. `--strict` exits 1 on changed/new/gone.
