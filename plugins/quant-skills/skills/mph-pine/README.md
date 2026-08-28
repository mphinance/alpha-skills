---
name: mph-pine
description: |
  Build TradingView Pine Script v6 indicators in the mphinance house style.
  Synthwave dashboard, faithful math, v6-compliant, no em dashes. Use when the
  brief asks to write, port, or extend a TradingView indicator or strategy.
triggers:
  - "pine script"
  - "tradingview indicator"
  - "write a pine indicator"
  - "port this to pine"
  - "/mph-pine"
---

# mph-pine

A skill for building TradingView Pine Script v6 indicators that look and behave
like the mphinance stable. It carries the v6 landmine checklist, the house-style
template (synthwave palette, grouped inputs, dashboard table plus a compressed
AI-readable payload row), reusable math (hand-rolled linreg with r2, residual
std, measured-move and reward/risk geometry, volume-confirm median, context-gated
candlestick patterns), and the hard rules (no em dashes anywhere, including code
comments, and clipboard handoff to TradingView since there is no offline compiler).

## Worked example

`channels.pine` is the reference build: **Ghost Channels**, an auto-fit parallel
trend channel ported from a Python scanner engine. It fits two parallel rails by
least squares, classifies the channel, and reports fit quality (r2), position,
width in ATR, rail touches, slope, and breakout state. On top of the geometry it
layers multi-timeframe confluence (dynamic `request.security`), candle reactions
gated to the rails, volume-confirmed breakouts versus traps, measured-move
targets, reward and risk, and a graded LONG / SHORT / WAIT verdict with a
confidence tally. Drop it into TradingView's Pine Editor to see the full pattern.

## How to use

Say "write a pine indicator for X" or "port this signal to Pine", or invoke
`/mph-pine`. The skill grounds on current v6 docs, ports any named source engine
faithfully first, builds in house style, runs the landmine and em-dash checks,
then hands the finished script to you on the clipboard for a paste into
TradingView. There is no offline Pine compiler, so that paste is the verification
step.
