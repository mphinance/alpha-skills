---
name: value-complex
description: >-
  Avantis value-factor tracker — small-cap (AVUV) and large-cap (AVLV) value in
  one read, straight from TickerTrace's per-fund holdings. Groups by fund tier and
  by position lifecycle (new/exited, conviction tilt, up-streaks), ranked by
  weight, and surfaces the sector themes both funds agree on. Use when the user
  asks "what's the value factor doing", "what did AVUV/AVLV add", "new adds in
  value", "what are the value funds buying", "value complex", or wants the
  small-vs-large value read.
---

# Value Complex — Avantis small + large value, by weight

This skill reads Avantis's two flagship value ETFs straight from TickerTrace's
**per-fund** endpoint (`/fund/<TICKER>`) and lays out what changed under the hood,
grouped the way the value factor actually moves:

- **AVUV** — small-cap value ($12.5B, ~794 holdings) — the flagship.
- **AVLV** — large-cap value ($3.2B, ~272 holdings).

> This is the per-fund holdings view that the daily **stock-recap** skill does
> *not* pull. stock-recap only hits TickerTrace's cross-fund aggregates
> (`/briefing`, `/institutional`, `/divergences`). This skill is the deep,
> by-weight, per-fund value read.

## What it groups, and why

For **each fund** (small tier → large tier), three lifecycle buckets:

1. **🆕 New / Exited** — positions TickerTrace flags `type=NEW` or `REMOVED`.
   Passive Avantis funds rarely open or close a name day-to-day, so when they do
   it's meaningful. This is the literal "new adds."
2. **📈 Conviction tilt** — active over/under-weighting, **inflow-stripped.**
   Every name in an inflow day shows a positive `sharesDelta` (new money buys the
   whole book pro-rata), so raw adds are noise. We compute each name's share growth
   `sharesDelta/previousShares`, take the **fund-wide median as the inflow tide,**
   and rank by the *excess* over that tide. Positive excess = the fund is genuinely
   leaning *into* the name beyond mechanical inflow; negative = leaning out.
3. **🔥 Up-streaks** — names on multi-day winning runs (TickerTrace `streaks`).
   This is the cleanest momentum signal — independent of fund mechanics entirely.

Then the payoff, **🔗 cross-tier synthesis:**
- **Sector convergence** — sectors that are streaking *and/or* tilting up in
  **both** the small and large fund. (Exact-ticker overlap is rare because the
  funds hold different cap tiers, so convergence is read at the sector/theme
  level — e.g. "transports leading in both.")
- **Flow tell** — all-buys with zero trims = **inflows into value** (creations,
  risk-on); a genuine mix of adds and trims = active rebalancing.

## How to run it

```bash
node "$HOME/.claude/skills/value-complex/scripts/gather.mjs"
```

- Writes `runs/<date_time>/report.md` + `raw/fund_AVUV.json`, `raw/fund_AVLV.json`.
- Prints the report to stdout and a final JSON line with `{reportPath, rawDir}`.
- No key needed — `/fund/<TICKER>` is public on TickerTrace. Presents a browser
  User-Agent (the edge WAF 403s a bare Node UA). ~5–10s.
- Override the base with `TICKERTRACE_API_URL`; funds with `VC_FUNDS=AVUV,AVLV,AVMV`.

## Present it to Mike

Read the generated `report.md` and give a tight read, in this order:

1. **The flow tell first** — are both funds taking inflows (value getting bought)
   or net trimming? That frames everything.
2. **New / Exited** names per fund — rare, so always call them out by name.
3. **Conviction tilt** — the inflow-stripped over-weights. These are the names the
   fund is actually leaning into, not just buying with the tide. Name the top 3–4
   per tier and what sector they're in.
4. **Streaks** — the momentum leaders, longest runs first.
5. **The cross-tier theme** — the one or two sectors strong in *both* small and
   large value. This is the headline ("the whole value complex is leaning into X").
   Tie it to the tape: what's it rotating *out of* (usually mega-cap growth).

## Notes / gotchas

- **`weightDelta` is not a clean signal on its own** — it blends price drift with
  share-count change. The report leads with the **inflow-stripped excess** instead;
  it shows weightDelta as secondary context only. Don't present weightDelta as
  "conviction" without the excess check.
- **Data is daily and can lag** — the report prints TickerTrace's `asOfDate`;
  surface it so Mike knows how fresh it is.
- **Cross-tier convergence is sector-level, not ticker-level** — small and large
  funds rarely share a ticker; agreement shows up as a shared *theme*.
- Each run is a point-in-time snapshot under `runs/`; nothing is overwritten and
  old folders are safe to delete (gitignored under `.claude/`).
