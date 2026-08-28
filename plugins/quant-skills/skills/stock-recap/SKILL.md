---
name: stock-recap
description: >-
  Daily market recap + convergence-ranked stock shortlist for TraderDaddy Pro.
  Runs ALL screeners at default settings, pulls the biggest options flows / smart
  money, new CBOE option listings, and hedge-fund (13F) activity, then finds the
  short list of names that multiple independent sources agree on — with technicals.
  Use when the user asks to "find good stocks", wants a "market recap", "what's
  flowing", "what are the funds doing", "run the screeners", "any setups", or
  "what should I be looking at" for trading ideas.
---

# Stock Recap — convergence-ranked picks

This skill produces a market recap and a **short list of stocks the data agrees on**,
each with technicals. It pulls four independent legs and ranks names by how many of
them point at the same ticker (equal-blend convergence):

1. **Screeners** — all 10 TraderDaddy Pro screeners at their default settings
   (Momentum Pullback, Gamma Scan, Coiled Springs, Daily Cuts, CSP Wheel, LEAPS,
   Leveraged, Small-Cap, Volatility Surge, Bullish Pullback).
2. **Options flow** — the biggest premium / smart-money unusual activity today,
   including the `INSTITUTIONAL_ALPHA` tier and repeat-strike conviction.
3. **New CBOE option listings** — names that just became optionable.
4. **Hedge funds (13F)** — TickerTrace top buys/sells, **cross-fund convergence**
   (multiple funds into the same name), and divergences.

It surfaces a **dedicated under-$100 section** so the list isn't all $700+
mega-caps. **The visual read lives on Ghost Flow (TradingView), not here** — the
recap is the data layer; Ghost Flow is the picture (see "Reading the charts" below).

It opens with a **regime gate** + **week-ahead block** — the Sunday-night context
a daily recap can't give you (all from the NEW dev API, `api.traderdaddy.pro/api/v1`,
`X-API-Key` in repo-root `.env_td_api`; every leg is best-effort and degrades alone):

- **🔴/🟠/🟡/🟢 Regime banner** — blends index put/call (SPY/QQQ/IWM) with SPY net
  gamma into a RISK-OFF → RISK-ON score. In a **RISK-OFF / negative-gamma** tape
  the convergence bar auto-tightens (names need one extra agreeing leg before they
  make the shortlist).
- **🗓️ The Week Ahead** — the macro clock (CPI/NFP/FOMC etc., flagged by impact), a
  **hinge-event** call-out, **⚠️ earnings landmines** (shortlist names that report
  this week — a swing entry into a print is a coin-flip, tagged in the Edge column
  and detail), and a one-line **sector tilt** (which sectors money leaned into/out of).
- **📋 Track record** — a one-line forward hit-rate from `score_history.mjs` (below),
  so the list carries its own honesty check.

> **Mike's edge:** his best picks come from **Momentum Pullback names that have
> ALREADY started recovering** — not the ones still buried in the hole. The script
> has a dedicated **Recovery Watch** section that flags pullback names where the
> turn is confirmed on the tape: **RSI reclaimed bullish (≥50 / bullish zone),
> price back above the 21EMA, week no longer bleeding, A/B entry grade.** It
> deliberately EXCLUDES deep-oversold names crossing up inside a downtrend — Ghost
> Flow grades those SHORT (they're bounce candidates, not longs; MIDD/CRS on
> 2026-07-19 were the lesson). It marks which recoveries already have bullish flow
> and fund buying behind them. Always call this out — and if the list is empty in a
> weak tape, say so plainly (nothing to chase beats a list of knives).
>
> **Four tiers of the turn (earliest → confirmed → graduated → tracking):**
> 1. **🌅 Turning Up** — the EARLIEST catch. Computes StochK(14/3) off chart-data
>    (screeners only give today's value) and fires when K just crossed **back up
>    through 40** after dipping below — the moment the turn starts, before RSI/EMA
>    confirm. FIG's 2026-06-30 reclaim at $18 (then +32%) is the archetype. Fresh
>    cross within `RECAP_TURN_LOOKBACK` (default 2) sessions, K ≤ `RECAP_TURN_KMAX`
>    (default 68, past which it's already extended). Scanned across **every**
>    screener (not just pullback) so a FIG-class name is caught at the cross — it
>    sat in csp-wheel before its 06-30 reclaim. A **Source** column shows which
>    screener(s) surfaced each name. Earlier = better price but noisier; always
>    tell Mike to confirm on Ghost Flow before sizing.
> 2. **🔄 Recovery Watch** — the CONFIRMED tier above (RSI≥50 + above 21EMA + week
>    not bleeding + A/B).
> 3. **🎓 Graduated from Watch** — a name that was on the PERSISTENT 👁️ Watch list
>    (dropped below 40 on a prior run) and just reclaimed 40. Shows was→now price,
>    % since it went on watch, and days tracked. 🔥 = fresh cross (≤2 sessions).
>    This is the payoff of tracking across runs: watch the drop, own the reclaim —
>    the exact FIG catch.
> 4. **👁️ Watch — persistent, cross-run** — names that FELL through 40. They land
>    here and **stay across runs** (even after they drop off every screener; those
>    show `off ✂️`) until they reclaim 40 (→ 🎓) or age out (`RECAP_WATCH_MAX_DAYS`,
>    default 21). NOT actionable while here. The loop: drop → watch → cross back up
>    → 🎓 Graduated. State lives in `runs/_watchlist.json`.
>
> Scan universe: the 40-line scan runs over the **full union of every screener's
> names** (any name that landed on ≥1 screener this run, ~170 names), so a FIG-
> class name is caught at its cross even if it's not a pullback name yet. New watch
> slots are earned by **pullback** names only (keeps the store tight), but once on
> the list a name is tracked purely off StochK — so it's never lost between the
> drop and the reclaim, even after it leaves every screener. Set
> `RECAP_DEBUG_WATCH=1` to log the store-only fetch each run.

## How to run it

1. Run the gather script from the repo root:

   ```bash
   node .claude/skills/stock-recap/scripts/gather.mjs
   ```

   It writes a timestamped folder under `.claude/skills/stock-recap/runs/<date_time>/`
   containing `report.md` (the full recap) and `raw/*.json` (every raw API pull,
   for backtesting or a deeper look). It also prints the report to stdout and a
   final JSON line with `{reportPath, rawDir, shortlist, health}`.

   - Takes ~30–90s (screeners are the slow part; they're cached 5 min server-side).
   - No setup needed: it auto-reads `AGENT_API_KEY` from the repo-root
     `.env_agent_api`, hits **production** (Railway + TickerTrace), and presents a
     browser User-Agent (the edge WAF 403s the bare Node UA).

   **Weekly mode (Sunday night):** prefix `RECAP_WINDOW=week`:

   ```bash
   RECAP_WINDOW=week node .claude/skills/stock-recap/scripts/gather.mjs
   ```

   This widens the flow window to the whole week and tightens the premium/score
   thresholds (weekly flow is noisier), and re-titles the report **"Sunday Setup —
   Week Ahead."** The regime gate + week-ahead calendar render in either mode, but
   they're what make the weekly run a real Sunday list. Default (no env) is the
   daily `today` recap.

2. **Cron / commit-to-history** — for the scheduled daily run use the wrapper:

   ```bash
   node .claude/skills/stock-recap/scripts/run_and_commit.mjs
   ```

   It runs `gather.mjs`, snapshots the output into the **git-tracked** `history/`
   dir — `history/<YYYY-MM-DD>.md` (full report), `history/<YYYY-MM-DD>.json`
   (compact shortlist + health + watch-list), and `history/_watchlist.json` (the
   persistent store snapshot) — then `git commit`s ONLY those paths (pathspec-
   restricted, so the rest of the working tree is never swept in) and **pushes** to
   origin (push failure is non-fatal — the commit stays saved locally). Same-day
   reruns overwrite the day's files; git keeps the diff history. The
   run dirs under `runs/` stay gitignored; `history/*.json` is un-ignored via a
   `.gitignore` negation. Disclaw cron **`stock-recap daily (commit history)`**
   (job `8f0675b4`, `0 17 * * 1-5` — weekday 5pm ET, post-close) invokes this.

2. **Read the generated `report.md`** (the path is in the script's final output).

3. **ALWAYS eyeball the charts before presenting.** Render the shortlist + tier
   names and *actually read the PNGs* — never present off the tables alone. On
   2026-08-02 this reversed 5 of 8 calls in one run.

   ```bash
   cd .claude/skills/stock-recap
   node scripts/render_chart.mjs ZION GOOGL BMNR --out /tmp/recap_charts_<date>
   node scripts/render_chart.mjs ORCL NKE --days 300 --out /tmp/recap_charts_<date>/long
   ```

   Charts render as SVG in headless chromium, in the Gamma Map palette, with live
   TD Pro dealer levels drawn on: red walls, green support, amber PIN, purple
   dashed gamma flip, OI on every label. Default window is ~4 months (`--days 88`).
   Pass `--no-gex` to skip the options-chain fetch.

   **Use `--days 300` on anything you're about to call a downtrend or a
   breakout.** 90 days is not enough to see a multi-month trendline, and that
   trendline IS Mike's #1 setup. The two views can disagree completely: at 90d
   NKE looked like dead chop under a falling 55EMA; at 300d it's a four-month
   base with a firm floor and flattening EMAs, coiling right under the descending
   line off the peak. Mike caught that and I hadn't. Conversely ORCL looked like
   a bounce at 90d and a *worse* accelerating breakdown at 300d.

   **The distinction that matters — decelerating base vs active waterfall:**
   - **Setup:** lower highs, but the decline has *flattened*, EMAs going
     horizontal, a floor tested repeatedly, price coiling under the trendline.
     Not triggered until it closes above the line, but it's worth watching.
   - **Knife:** still making *lower lows* (esp. undercutting the prior major
     low), EMAs fanned out and steeply falling, 200SMA rolling over overhead.
     No amount of RSI/Stoch turn makes this a long.

   Table artifacts the charts catch, every time:
   - **ADX has no direction.** High ADX on a falling stock = strong DOWNtrend.
     Never cite it as bullish without the chart (ORCL, ADX 41, in freefall).
   - **A weekly % can hide a gap.** RDDT's "-21% on the week" was ONE gap
     candle on 5x volume, the most recent bar. Fresh gap ≠ pullback.
   - **Dead tickers score A+.** Now filtered by `DEAD_RANGE_PCT`, but sanity-check
     the y-axis range anyway.

   Then send the PNGs to Discord grouped as keep-vs-cut so Mike sees what you saw.

4. **Ghost Flow is still the confirm.** The report ships no PNGs by design; Mike
   confirms the visual on **Ghost Flow**
   (his TradingView indicator), which encodes the whole decision — GRADE, W GATE,
   FLOW (CMF), SQUEEZE, %R EXHAUST, VOL PREMIUM, ADX/RSI, BOUNCE, ATR-based RISK
   sizing, and gamma walls on the price axis — far past what a bare candle+EMA
   render can show. When presenting the recap, tell Mike which shortlist names to
   **pull up on Ghost Flow** and what to look for (is the W-GATE open or WAIT, is
   FLOW positive, is it bouncing or rolling). The data tables here are the screen;
   Ghost Flow is the confirm — your own chart read in step 3 is the filter that
   decides what's even worth him opening.

5. **Present a tight, plain-English recap to Mike** — don't just dump the file.
   Lead with what matters:
   - The 2–4 **highest-conviction names** — judged on the CHART first, rank
     second. If the top-ranked name has a bad chart, say so and lead with the
     one that doesn't. Name which to **confirm on Ghost Flow** before sizing.
   - **Anything you're cutting from the shortlist and why.** The list is a
     starting universe, not a recommendation.
   - The **Recovery Watch** — Momentum Pullback names that have **already reclaimed**
     (RSI back ≥50, above the 21EMA, week not bleeding), especially ones with flow 🟢
     and fund ✅ confirmation (his setup). NOT deep-oversold names in a downtrend.
     Point him at Ghost Flow to confirm (W-GATE open, FLOW positive, bouncing not
     rolling). If it's empty, say so — nothing to chase beats a list of knives.
   - The **💵 Under-$100** picks — Mike specifically wants accessible names, not
     just $700+ mega-caps. Always surface a few.
   - A one-line **flow/fund tone** read (net bullish vs bearish premium; what the
     funds are buying/selling; any notable cross-fund convergence).
   - **⚠️ Conflicts** — names where bullish sources disagree with bearish flow or
     fund selling (e.g. funds buying but options heavily bearish). Flag, don't bury.
   - New CBOE listings only if there's something worth noting.

6. Point Mike at the saved `report.md` for the full tables/charts, and mention the
   `raw/` JSON is there if he wants to dig in or backtest.

## Scoring the track record (`score_history.mjs`)

The recap grades itself. After runs have aged a forward window (default 5 trading
days), run:

```bash
node .claude/skills/stock-recap/scripts/score_history.mjs
```

For every old-enough run it looks up each shortlist name's price N trading days
later (same source the run used — `/api/agent/ticker/:symbol/chart-data`), computes
the forward return, and writes `runs/<stamp>/scored.json` plus a rolling
`runs/_scorecard.json`. The next `gather.mjs` run reads `_scorecard.json` back in
and prints the **📋 Track record** line. It's **idempotent** (a scored run is
cached; pass `--rescore` to redo) and best-effort. Buckets the results by
**Reversal-Watch vs base** and by **leg count**. Tune with `--horizon N`.

> ⚠️ **The convergence thesis did not survive contact with the data.** At 401
> picks / 30 runs the leg-count buckets are **inverted**: 2-leg 48% · 3-leg 26%
> · 4+-leg 17%, against a 47% base. More agreement predicts WORSE forward
> returns. Working theory: legs past two come from flow + funds, which stack
> correlated mega-cap noise rather than confirming a setup. As of 2026-08-02
> `LEG_RANK_CAP = 2` caps the rank contribution and a confirmed reversal (51%,
> the only bucket beating base) outranks raw agreement. Legs still **gate** the
> shortlist; they no longer buy position on it. Re-check as the sample grows —
> if it flips back, raise the cap.
Worth running weekly (e.g. before the Sunday pull) so the track record stays fresh.

## Tuning (optional env vars)

- `RECAP_WINDOW=week` — weekly Sunday-night mode (default `today`). Widens the flow
  window and tightens flow thresholds; re-titles to "Sunday Setup — Week Ahead."
- `RECAP_SHORTLIST=20` — shortlist size (default 15).
- `RECAP_MAX_PRICE=50` — cutoff for the under-$N affordable section (default 100).
- `RECAP_FLOW_MIN_SCORE` / `RECAP_FLOW_MIN_PREMIUM` — flow filter floors (weekly
  defaults to a higher premium floor since weekly flow is noisier).
- `RECAP_TIMEOUT_MS=90000` — per-request timeout (default 60s).
- `TD_API_URL` / `TICKERTRACE_API_URL` / `TD_DEV_API_URL` — override base URLs (the
  last is the NEW dev plane backing regime + week-ahead; key in `.env_td_api`).

## Notes / gotchas

- **Convergence is directional.** Only bullish-aligned legs (screener hit, bullish
  flow, fund buying, cross-fund buying, new-CBOE) add to a name's score. Bearish
  flow or fund selling against a bullish name is recorded as a **conflict**, not
  agreement, and is penalised in the ranking. This is a long-idea finder.
- **Technicals enrichment:** names that arrive via flow/funds only (no technical
  screener) are back-filled from `/api/agent/ticker/:symbol` (RSI, ADX, EMA stack,
  call/put walls, expected move). Stochastic isn't available there, so the Stoch
  column shows `—` for those.
- **13F data is TickerTrace**, not TD Pro's `/api/institutional/*` (the agent key
  is scoped to `/api/agent/*` and can't reach it). If TickerTrace is down, the
  hedge-fund leg degrades gracefully and the rest still runs.
- Each run is a fresh point-in-time snapshot; nothing is overwritten. Old run
  folders are safe to delete (they're gitignored under `.claude/`).
- **Charts are `scripts/render_chart.mjs`** — hand-built SVG rendered in headless
  chromium (playwright), styled to match the Gamma Map product in `docs/gex-chart/`
  and carrying live TD Pro dealer levels. Node only; no venv, no matplotlib. The
  earlier "no chart PNGs by design" call was wrong: the render was ugly, not
  useless. Reading the charts reversed 5 of 8 calls in a single run on 2026-08-02.
- Note that `dealer-hud` is a *browser extension* that draws over TradingView, so
  there is no renderer in it to lift. Copy the look from `docs/gex-chart/` instead.
