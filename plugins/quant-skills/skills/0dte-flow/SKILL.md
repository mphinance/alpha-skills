---
name: 0dte-flow
description: >-
  0DTE day-trading playbook for a small account — Ghost Alpha signals into
  Tradier XSP (Mini-SPX) same-day options with strict IFTTT entry/exit rules and
  hard risk guardrails. Use when Michael wants to run a 0DTE session, size a
  contract, decide whether a signal qualifies, or apply the exit cascade. This is
  a DECISION-SUPPORT playbook — it drafts the plan; Michael places every order.
---

# 0DTE Day-Trading Flow

Ghost Alpha A+/A signals → Tradier XSP 0DTE options → same-day close.

## Why XSP

XSP (Mini-SPX) is 1/10th of SPX, **cash-settled / European (no assignment
risk)**, with 0DTE M/W/F on Tradier. Cheap enough for a small account.
**Fallback:** if XSP isn't tradeable, use SPY 5+ OTM ($0.10–$0.30).

## Position sizing (example: $75 account)

| Rule | Value |
|------|-------|
| Max per trade | $30 |
| Buffer | $10 |
| Trades per day | 2 sequential (never concurrent) |
| Strike | 2–3 OTM ($0.15–$0.50/contract) |
| Max daily loss | $60 (2 full losers = walk away) |

## Entry — ALL must hold

```
Ghost Alpha Grade ≥ B on SPY 5min
AND signal = mega_bull OR mega_bear
AND RVOL > 1.2
AND time 9:30–11:30 AM ET
AND trend_age < 15 bars
AND no open 0DTE position
```

## Exit cascade — first match wins

| # | Type | IF | THEN |
|---|------|----|------|
| S1 | 🔴 Hard stop | Loss ≥ -50% | SELL (non-negotiable) |
| S2 | 🔴 Grade death | Grade → D/F | SELL (thesis dead) |
| S3 | 🔴 Reversal | Signal flips bull↔bear | SELL (wrong side) |
| T1 | ⏰ EOD | Time ≥ 2:30 PM ET | SELL (theta cliff) |
| P1 | 🟢 Double | Gain ≥ +100% | SELL (take the W) |
| P2 | 🟢 Fading | Gain ≥ +30% AND Grade → C | SELL (lock it) |
| P3 | 🟢 Afternoon | Gain ≥ +50% AND time > 1 PM | SELL (theta) |
| T2 | ⏰ Dead money | Time ≥ 12 PM AND ±10% | SELL (free up trade 2) |

**Re-entry:** Trade 2 only if Trade 1 closed, buying power ≥ $20, and a new
A+/A signal fires. Two losers → DONE for the day.

## Guardrails (NON-NEGOTIABLE)

Max 1 open position · auto-close 2:30 PM ET · no averaging down EVER ·
Grade floor B · entries 9:30–11:30 AM only · **no Friday 0DTE** (witching risk).

## Tradier order reference

Option symbol format: `XSP260310C00675000` = XSP · 2026-03-10 · Call · $675.

```bash
# Today's chain
curl -s -H "Authorization: Bearer $TRADIER_TOKEN" \
  "https://api.tradier.com/v1/markets/options/chains?symbol=XSP&expiration=$(date +%Y-%m-%d)"

# Buy to open
curl -s -X POST -H "Authorization: Bearer $TRADIER_TOKEN" \
  "https://api.tradier.com/v1/accounts/$ACCOUNT_ID/orders" \
  -d "class=option&symbol=XSP&option_symbol=XSP260310C00675000&side=buy_to_open&quantity=1&type=limit&price=0.35&duration=day"
```

> Pull `TRADIER_TOKEN` / `ACCOUNT_ID` from VaultGuard — see [AGENTS.md](../../../AGENTS.md).

## Pre-session checklist

- [ ] Venus healthy; buying power confirmed
- [ ] XSP chain loads on Tradier; L2 options active
- [ ] Ghost Alpha on SPY 5min in TradingView
- [ ] First mega signal → pick 2–3 OTM, premium $0.15–$0.50, Grade ≥ B
- [ ] Apply exit cascade · screenshot entry for blog · close all by 2:30 PM ET · log results

## Source

Full guide: [`0DTE_TRADING_FLOW.md`](../../../0DTE_TRADING_FLOW.md).

*"0DTE options are like Mike Tyson — rich in 5 minutes or knocked out in 3. The
difference is whether you have a plan when you walk in the ring." — Sam 👻*
