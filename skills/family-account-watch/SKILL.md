---
name: family-account-watch
description: Daily read-only check of connected family brokerage accounts plus market context, ending in a short list of what to do tomorrow. Use when asked "what should we do tomorrow", for the daily account check, or to review holdings, earnings, dividend dates and expiring options on the connected accounts. Never trades.
---

# Family Account Watch

Read-only daily routine. Output is a short "Tomorrow" list, or "Nothing to do tomorrow." Never trade, never edit watchlists, never contact anyone but the owner.

## Order of work

1. **Can you see the accounts?** Look for the account tools in your tool list (positions, balances, activity). If they are missing or return nothing, say "I cannot see the accounts yet", give market context only, and stop. Do not guess holdings.
2. **Freshness.** Record the as-of time on every snapshot. If a snapshot is older than a day, or a history import looks unfinished (open-position counts far below the broker's), say so first and treat the rest as provisional.
3. **Normalize.** Treat BRK.B and BRK/B as one security. Mutual funds may come back with no instrument type; they are holdings. Options value = quantity x last price x 100. Totals are "estimated": the feed gives cash and buying power, not net liquidation value.
4. **Market context** (only what bears on held names): `get_market_health`, `get_macro_regime`, `get_economic_calendar`.
5. **Held-name checks:** `get_earnings_flow` for earnings dates, `get_dividend_calendar` for ex-dividend dates, `get_ticker_news` for a held name that moved sharply, `get_iv_rank` before suggesting any option idea.
6. **Compare to the last check.** Keep notes with the memory tool: date, flags raised, snapshot as-of times. Only report what is new or materially changed. Never repeat the same warning daily.

## What counts as a flag

- Earnings or ex-dividend date within the next trading days on a held name, with the date and source.
- A gap or move beyond 3% against an explicit prior close (state both prices and times).
- Position concentration crossing a limit the owner has set (ask once if none is stored).
- An option expiring within 7 days, or assignment risk (in the money near expiry, ex-dividend on a short call).
- Dividend cut or suspension on a held name: raise it as REVIEW for the owner. Never recommend selling on a machine trigger alone.
- A failed, stale, or partial sync: report it as a monitoring failure. "No alerts" never proves the accounts are safe.

## Learning from history

If transaction history is available, study it privately to learn the owner's habits and tune what you flag. Never quote old mistakes or losses back in an answer.

## Income ideas (only on request)

Cash-secured puts or covered calls only after confirming unrestricted shares, option permissions, earnings and ex-dividend timing, and willingness to be assigned. Show premium, capped upside, assignment case, downside, and the yield denominator and day count. Quotes may be stale outside market hours; require a recheck before acting.

## Output format

```
Tomorrow (as of <time>, accounts <fresh|stale|not visible>)
1. <ticker/account>: <what>, <why>, <source and date>
...
```
or `Nothing to do tomorrow.` Concise, numbers first, no boilerplate, no em dashes.
