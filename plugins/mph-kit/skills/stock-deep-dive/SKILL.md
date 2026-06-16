---
name: stock-deep-dive
description: >-
  The deepest single-stock pull we have — everything on ONE ticker in one shot, so
  when someone asks "do you like PLTR down here?" you can just check instead of
  looking it all up by hand. Pulls TickerTrace 13F ownership + recent fund changes,
  full technicals (RSI/ADX/EMA stack/stoch/MACD/fibs/pivots/keltner), complete
  options positioning (max pain, call/put walls, expected move, IV skew, OI by
  strike), recent options flow, renders a 90-day chart, and (you) WebSearch recent
  news/catalysts — then deliver a plain-English verdict. Use when the user asks
  "do you like X here / down here", "what's the story on X", "should I buy X",
  "pull everything on X", "deep dive X", "is X a buy", or names a single ticker and
  wants the full read.
---

# Stock Deep Dive — everything on one ticker

This is the **single-stock** counterpart to `stock-recap` (which scans the whole
market). Here the user hands you **one ticker** and wants the complete read fast.
It exists so Michael can ask *you* "do you like PLTR down here?" instead of pulling
up six tabs of technicals, options, ownership, and news himself.

It pulls four legs for the ticker and you add a fifth (news):

1. **Technicals** — TD Pro `/api/agent/ticker/:SYM`: RSI, ADX, stoch, MACD, ATR,
   the full EMA/SMA ladder (8/21/55/89/50/200), trend status, EMA stack, buy-zone,
   squeeze ratio, Williams %R, CCI, Bollinger %B, pivots (S2→R2), fib retrace
   (.382/.500/.618), Keltner channel, 90-day range, and bounce state.
2. **Options positioning** — same endpoint: max pain, call wall (resistance), put
   wall (support), expected move to next expiry, IV skew + dealer sentiment,
   put/call OI ratio, and the biggest open-interest strikes (call vs put OI).
3. **Options flow** — TD Pro `/api/agent/unusual-activity?ticker=SYM` over the last
   week: net bullish vs bearish premium, call vs put premium, the largest trades,
   institutional-alpha tier, and repeat-strike conviction.
4. **Institutional ownership** — TickerTrace `/ticker/:SYM`: which funds/ETFs hold
   it and at what weight, plus **recent 13F changes** (adds/trims, including option
   overlays). Read the provider + type — a YieldMax/Roundhill option overlay is
   income mechanics, not a directional conviction bet.
5. **News / catalysts** — *not in the script* (no TD Pro news endpoint). After the
   pull, **you WebSearch** for recent headlines, earnings dates, guidance, analyst
   moves — whatever explains where price is — and fold it into the verdict.

It also **renders a 90-day candlestick chart** (reusing the `stock-recap` skill's
Python venv + `render_chart.py` — no second install).

## How to run it

1. Run the dossier script with the ticker(s). Works from any directory — the
   absolute path resolves the symlink back into the mphinance repo, so the API key
   and the sibling `stock-recap` chart venv are found automatically:

   ```bash
   node "$HOME/.claude/skills/stock-deep-dive/scripts/dossier.mjs" PLTR
   ```

   - One ticker is the norm; pass several (`… dossier.mjs PLTR NVDA SOFI`) for one
     dossier each.
   - Takes ~5–15s per ticker. Auto-reads `AGENT_API_KEY` from `.env_agent_api`,
     hits production (TD Pro + TickerTrace), presents a browser UA.
   - Writes `runs/<TICKERS>_<date_time>/<SYM>_dossier.md`, `charts/<SYM>.png`, and
     `raw/<SYM>_*.json`. Prints the dossier to stdout and a final JSON line with
     `{outDir, results}`.

2. **Read the generated `<SYM>_dossier.md`** for the full tables.

3. **Open the chart PNG** with the Read tool and actually look at it — 90-day
   candles + EMA 8/21/55 + SMA200 + volume + RSI. Judge trend, structure, where
   price sits vs the fast EMAs (pullback-to-support vs extended vs broken). The
   visual read often **overrides the indicator table** — e.g. a name can look
   oversold on RSI but the chart shows a clean breakdown you shouldn't catch.

4. **WebSearch for recent news/catalysts** on the ticker — last few weeks: earnings
   (and the next earnings date), guidance, analyst rating/PT changes, sector news,
   anything that explains the current price. *News follows price* — find what moved
   it. (In any public/Substack write-up, the AI is "Sam," never "Claude.")

5. **Deliver the verdict to Michael — plain English, blunt, with a recommendation.**
   Don't dump the file. Answer the question he actually asked ("do you like it
   here?"). Structure:
   - **One-line take** — bull/bear/neutral and why, in a sentence.
   - **The setup** — where price is in its range, the trend, the chart read, the
     levels that matter (put wall / EMA21 / SMA200 as support; call wall / pivots /
     fib as resistance). Give a *where-would-you-buy* and *where's-it-wrong* level.
   - **What the options say** — flow lean (net premium direction), dealer
     positioning (max pain, walls, IV skew), expected move. Is smart money leaning?
   - **Ownership** — are funds adding or trimming? Flag if the "ownership" is mostly
     option-overlay/income ETFs (not real conviction).
   - **The catalyst / risk** — the news read; next earnings date; what could break
     the thesis.
   - **Bottom line** — would you buy it here, wait for a level, or pass. Be willing
     to say "no, not here." Push back; don't just validate the question.

## Notes / gotchas

- **This is a read, not a recommendation engine.** It aggregates data; the judgment
  is yours. Always reconcile the indicator table against the chart and the news —
  if they disagree, say so.
- **TickerTrace coverage is funds/ETFs**, including thematic and option-overlay
  products. High `fundCount` ≠ high conviction. Read providers: ARK/whale long-only
  adds mean something different than a YieldMax covered-call overlay.
- **No news endpoint** — the WebSearch in step 4 is not optional; without it the
  dossier is half-blind. Where price sits only makes sense next to *why*.
- **Flow timeframe** defaults to `week`. Override with `DD_FLOW_TIMEFRAME=today`
  (or `month`) for a tighter/wider flow window.
- **Auth/UA:** same plumbing as `stock-recap` — `AGENT_API_KEY` from
  `.env_agent_api`, browser UA (the edge WAF 403s the bare Node UA). The
  `ticker=` query param is what filters flow by symbol (`symbol=` is ignored).
- **Charts** reuse `stock-recap/.venv` + `render_chart.py`. If `stock-recap` isn't
  present or its venv is missing, the chart step is skipped and the data dossier
  still completes. Both skills live side-by-side in the repo's `.claude/skills/`.
- Each run is a fresh point-in-time snapshot; run folders are gitignored under
  `.claude/` and safe to delete.
