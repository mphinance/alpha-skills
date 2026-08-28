---
name: momentum-squeeze
description: >-
  Two-phase equity momentum playbook — find coiled "Volatility Squeeze" stocks
  ready to break out, then buy confirmed multi-timeframe uptrends on pullback.
  Use when Michael asks to scan for squeezes, find pullback entries, evaluate a
  ticker against the momentum cycle, or decide where a stock sits in the
  coil → breakout → pullback → re-coil loop.
---

# Momentum & Squeeze Strategy

Two complementary strategies that capture different phases of a stock's momentum
cycle. A name typically rotates: **Squeeze → breakout → Momentum pullback →
trend exhaustion → re-coil → Squeeze** again.

## 1. Volatility Squeeze ("The Snap") — pre-breakout

Find stocks quietly coiling, ready to explode.

| Condition | Meaning |
|-----------|---------|
| `SqueezeRatio < 1.0` | Daily ATR compressed vs weekly ATR |
| `SqueezeRatio < 0.7` | Extremely tight — maximum coil |
| EMA stack aligned | 8 > 21 > 34 > 55 > 89 (bullish bias) |
| Not at 52wk high | Avoid flatlined M&A targets |
| Rel Volume ≥ 1.3x | Starting to wake up |

```
SqueezeRatio = ATR(14) / (ATR_Weekly / 2)
  < 0.70  → 🔋 Tight squeeze (ready to snap)
  < 0.85  → ⚡ Moderate
  < 1.00  → 📊 Light compression
  > 1.00  → ❌ Expanded (not squeezed)
```

**Entry signals:** Volume Spark (1.5x+), Deep Coil (ADX < 15), Price at EMA.

**Thesis:** *"Gone quiet. Daily volatility compressed against the weekly
baseline. EMAs bullishly stacked. Volume picking up. Ready to snap."*

## 2. Momentum with Pullback — mid-trend

Find confirmed uptrends that pulled back to a buyable entry. Requires **triple
timeframe EMA alignment** (8 > 21 > 34 > 55 > 89 on Daily AND Weekly AND
Monthly = confirmed mega-trend).

| Pullback filter | Purpose |
|-----------------|---------|
| SMA50 > EMA200 (D/W/M) | Uptrend on all timeframes |
| Stochastic < 40 | Oscillator oversold (the dip) |
| Within 1 ATR of EMA21 | Not overextended |
| ADX 20–40 | Trending but not exhausted |

**Thesis:** *"Powerful multi-timeframe uptrend, just pulled back to the 21 EMA,
stochastic oversold. Perfect dip buy."*

## Comparison

| Aspect | Squeeze | Momentum Pullback |
|--------|---------|-------------------|
| Stage | Pre-breakout | Mid-trend |
| Volatility | Compressed | Normal/Expanded |
| Stochastic | Any | < 40 |
| Risk / Reward | Higher / Higher | Lower / Moderate |
| Timeframe | Daily only | Daily + Weekly + Monthly |

## Weekly workflow

1. **Weekend:** run Volatility Squeeze → watchlist the coiled names.
2. **Mon–Fri:** monitor for breakouts (volume + close above resistance).
3. **Mid-week:** run Momentum with Pullback → dip entries in live trends.
4. **Manage:** stop below EMA21, trail as trend continues.
5. Trend exhausts → name returns to the Squeeze watchlist.

## Source

Full guide: [`MOMENTUM_SQUEEZE_GUIDE.md`](../../../MOMENTUM_SQUEEZE_GUIDE.md).
Strategy code lives in the screener project (`strategies/momentum.py`,
`strategies/volatility_squeeze.py`) — run via the `batch-scanner` skill.
