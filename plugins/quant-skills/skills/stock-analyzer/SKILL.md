---
name: stock-analyzer
description: >-
  ML-powered single-ticker analysis — Random Forest price-range prediction
  (5-day horizon) plus emoji-annotated technical insights for the Single Ticker
  Audit view. Use when Michael wants a price prediction, a read on one ticker's
  technicals, or to explain the audit view's prediction card and confidence.
---

# Stock Analyzer

Random Forest regression over technical indicators to predict a 5-day price
range and generate market insights for the Single Ticker Audit view.

## Usage

```python
from stock_analyzer import StockAnalyzer, generate_market_analysis

analyzer = StockAnalyzer()
data = analyzer.calculate_technical_indicators(ohlcv_df)
model_info = analyzer.train_prediction_model(data, horizon=5)
prediction = analyzer.predict_price_range(model_info, current_price=150.0)
insights = generate_market_analysis(data, ticker="AAPL")
```

## Requirements

Needs `pandas` and `scikit-learn`. Run with the repo-root venv, NOT bare `python3`:
```
.venv/bin/python -c "from stock_analyzer import StockAnalyzer, generate_market_analysis"
```
Verified: `./.venv/bin/python` has both. Bare `python3` does not, and the resulting
`ModuleNotFoundError: No module named 'pandas'` is the "skill seems broken" symptom,
not a code fault.

## Indicators

| Category | Indicators |
|----------|------------|
| Moving averages | SMA(20), SMA(50), EMA(12), EMA(26) |
| Momentum | RSI(14), MACD + signal + histogram |
| Volatility | Bollinger Bands(20,2), ATR(14) |
| Volume | Volume SMA(20), Volume Ratio |
| Oscillators | Stochastic %K, %D |

**ML features:** lag (close/volume/returns 1–5d back), rolling mean/std (5/10/20d),
price-vs-SMA20/50, 10/20d return volatility.
**Minimums:** 50 bars to train, 30 after split.

## Prediction output

```python
{ 'expected': 152.30, 'low': 148.50, 'high': 156.10,
  'expected_change_pct': 1.53, 'confidence': 0.72, 'horizon': 5 }
```

`low`/`high` = ±1 std dev across trees; `confidence` = inverse of relative
uncertainty (0–1).

## Insight categories

Price movement · RSI overbought/oversold · MA alignment · Bollinger extremes ·
MACD direction & crossovers · volume conviction. Returned as an emoji-annotated
list, e.g. `💡 RSI at 28.5 suggests oversold — potential buying opportunity`.

## Integration

`main.py → render_audit_view()`: fetch ~6mo daily (yfinance) → indicators →
train (if enough data) → prediction card (Low/Expected/High) → insights panel.

## Source

Full guide: [`STOCK_ANALYZER_README.md`](../../../STOCK_ANALYZER_README.md).
