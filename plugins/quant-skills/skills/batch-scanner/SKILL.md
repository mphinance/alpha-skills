---
name: batch-scanner
description: >-
  Run the full suite of stock-screening strategies in sequence and export
  results to Google Sheets (one tab per strategy). Use when Michael wants to run
  the nightly/weekend scans, refresh the screener tabs, run a specific strategy,
  or understand which strategies are available and what each surfaces.
---

# Batch Scanner

Runs every screening strategy in sequence and pushes results to Google Sheets
(one tab per strategy). Cron-ready for scheduled scans.

## Usage

```bash
python batch_scanner.py                 # run all → Sheets
python batch_scanner.py --dry-run       # print, don't send
python batch_scanner.py --strategies "Momentum with Pullback,MEME Screen"
python batch_scanner.py --list          # show valid strategy names
```

## Available strategies

| Strategy | Surfaces |
|----------|----------|
| Momentum with Pullback | Multi-timeframe EMA stack + oscillator pullback |
| Volatility Squeeze | Coiled stocks ready to break out (ATR compression) |
| MEME Screen | Top 30 by IV from top 200 by volume |
| Small Cap Multibaggers | Quality small caps, growth + positive FCF |
| Gamma Scan | Stocks near high open-interest option strikes |
| EMA Cross Momentum | Bullish EMA crossover |
| Bearish EMA Cross (Down) | Bearish EMA crossover |

> For the Squeeze / Momentum strategies' entry logic, see the
> [`momentum-squeeze`](../momentum-squeeze/SKILL.md) skill.

## Setup

1. `pip install pandas requests python-dotenv tradingview-screener yfinance scikit-learn`
2. Create `.env` with `GOOGLE_SHEETS_WEBHOOK=https://script.google.com/macros/s/<id>/exec`
3. Deploy `google_sheets_script_v2.js` as an Apps Script Web App
   (Execute as **Me**, access **Anyone**); copy the URL into `.env`.

## Cron (weekdays 4 PM)

```cron
0 16 * * 1-5 cd /path/to/project && .venv/bin/python batch_scanner.py >> logs/batch.log 2>&1
```

## Output columns

`ScanTime · Symbol · Company · WeekEnding · <strategy-specific> · CurrentPrice`
(live via `GOOGLEFINANCE`).

## Troubleshooting

| Issue | Fix |
|-------|-----|
| "GOOGLE_SHEETS_WEBHOOK not configured" | Create `.env` with the webhook URL |
| "Sheets error: 302" | Redeploy Apps Script with **Anyone** access |
| "Unknown strategy" | Run `--list` for valid names |
| Slow scans | MEME / Gamma fetch option data — expected |

## Source

Full guide: [`BATCH_SCANNER_README.md`](../../../BATCH_SCANNER_README.md).
