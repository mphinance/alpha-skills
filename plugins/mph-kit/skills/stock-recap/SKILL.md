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
3. **Bounce finder** — TD Pro's `/api/agent/bounce-finder`. `bounce_bottom` =
   oversold name curling up (a second, independent read on Mike's reversal edge);
   `bounce_top` = overbought exhaustion (tracked as a conflict, not a bullish leg).
4. **Earnings gaps** — TD Pro's `/api/earnings-gap`. Bullish gap-ups that are
   **holding** (positive intraday, not filling back through the open) count as a
   momentum leg; fading or bearish gaps are context/conflict only.
5. **New CBOE option listings** — names that just became optionable.
6. **Hedge funds (13F)** — TickerTrace top buys/sells, **cross-fund convergence**
   (multiple funds into the same name), and divergences.

It also **renders candlestick charts** (from our own 90-day OHLC data) for the
top picks + reversal names and a **dedicated under-$100 section** so the list
isn't all $700+ mega-caps.

> **Mike's edge:** his best picks come from **Momentum Pullback names once they
> START reversing out** of the pullback. The script has a dedicated **Reversal
> Watch** section that flags pullback names with a fresh stochastic crossover up
> from oversold + bullish RSI zone + A/B entry grade, and marks which of those
> already have bullish flow and fund buying behind them. Always call this out.

## How to run it

1. Run the gather script (works from any directory — the absolute path resolves
   the symlink back into the mphinance repo, so the API key and chart venv are
   found automatically):

   ```bash
   node "$HOME/.claude/skills/stock-recap/scripts/gather.mjs"
   ```

   It writes a timestamped folder under `stock-recap/runs/<date_time>/`
   containing `report.md` (the full recap) and `raw/*.json` (every raw API pull,
   for backtesting or a deeper look). It also prints the report to stdout and a
   final JSON line with `{reportPath, rawDir, shortlist, health}`.

   - Takes ~30–90s (screeners are the slow part; they're cached 5 min server-side).
   - No setup needed: it auto-reads `AGENT_API_KEY` from the repo-root
     `.env_agent_api`, hits **production** (Railway + TickerTrace), and presents a
     browser User-Agent (the edge WAF 403s the bare Node UA).

   The script auto-renders charts as part of the run (it shells out to the skill's
   Python venv — `.venv/bin/python scripts/render_chart.py`). No separate step.

2. **Read the generated `report.md`** (the path is in the script's final output).

3. **Open every chart PNG** listed in the report's **"📉 Charts rendered"**
   section with the Read tool and look at each one. The chart is 90-day candles +
   EMA 8/21/55 + SMA200 + volume + RSI. For each, judge: trend direction and
   strength, where price sits vs the fast EMAs (pullback to support vs extended),
   any structure (breakout, base, blow-off/exhaustion wick, lower-high rollover).
   The visual read often **overrides the indicator table** — e.g. a name can rank
   high on flow but the chart shows a parabolic blow-off you should not chase.

4. **Present a tight, plain-English recap to Mike** — don't just dump the file.
   Lead with what matters:
   - The 2–4 **highest-conviction names** (most aligned legs, no conflict), with
     their key technicals, **what their chart shows**, and why they're interesting.
   - The **Reversal Watch** — any Momentum Pullback names turning up, especially
     ones with flow 🟢 and fund ✅ confirmation (his setup). Use the charts to
     confirm the turn is real.
   - The **🪂 Bounce Finder** — fresh `bounce_bottom` oversold turns. A name in
     **both** Bounce Finder and Reversal Watch (or with flow/fund confirm) is the
     strongest oversold-turn — two independent scanners agreeing.
   - The **📈 Earnings Gaps** — bullish gap-ups, but **check the intraday column**:
     holding (✅) is momentum, fading (⚠️) is a trap. These have been some of
     Mike's best trades — always surface the holders.
   - The **💵 Under-$100** picks — Mike specifically wants accessible names, not
     just $700+ mega-caps. Always surface a few.
   - A one-line **flow/fund tone** read (net bullish vs bearish premium; what the
     funds are buying/selling; any notable cross-fund convergence).
   - **⚠️ Conflicts** — names where bullish sources disagree with bearish flow or
     fund selling (e.g. funds buying but options heavily bearish). Flag, don't bury.
   - New CBOE listings only if there's something worth noting.

5. Point Mike at the saved `report.md` for the full tables/charts, and mention the
   `raw/` JSON is there if he wants to dig in or backtest.

## Tuning (optional env vars)

- `RECAP_SHORTLIST=20` — shortlist size (default 15).
- `RECAP_MAX_PRICE=50` — cutoff for the under-$N affordable section (default 100).
- `RECAP_TIMEOUT_MS=90000` — per-request timeout (default 60s).
- `TD_API_URL` / `TICKERTRACE_API_URL` — override base URLs (e.g. point at
  `http://localhost:3001` for a local backend).

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
- **Charts** are rendered from our own `/api/agent/ticker/:symbol/chart-data`
  (90d OHLC + indicators) — no TradingView scraping, no session cookies, no
  account risk, no third-party chart API. If the chart step fails, the data
  recap still completes; the health table shows the render status.
- **One-time setup** (already done on this machine): a Python venv lives at
  `.venv/` with `mplfinance` + `pandas`. If it's missing (fresh clone), recreate:
  `python3 -m venv .venv && .venv/bin/pip install mplfinance pandas`.
