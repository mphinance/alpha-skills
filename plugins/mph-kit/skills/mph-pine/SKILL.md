---
name: mph-pine
description: Build TradingView Pine Script v6 indicators in Michael's house style. Synthwave dashboard, faithful math, v6-compliant, no em dashes. Triggers on "pine script", "tradingview indicator", "write a pine indicator", "/mph-pine".
---

# Mph Pine

Build TradingView Pine Script v6 indicators that look and behave like the mphinance house stable (channels.pine, ghost_dashboard.pine, ghost_alpha.pine). Faithful math, clean v6, a synthwave dashboard, and a compressed AI-readable payload row so Gemini or Sam can read the chart.

## When to invoke

Use when the user asks to build, port, or extend a TradingView indicator or strategy: "write a pine indicator", "tradingview indicator for X", "port this Python signal to Pine", "add alerts to my script", "/mph-pine". If the user names an existing engine (a Python scanner, a screener rule), treat that as the source of truth and port it faithfully before adding extras.

## Flow

1. **Ground on v6 first.** Pull current docs (the context7 / pine-script docs MCP, or tradingview.com/pine-script-docs) before writing. Do not trust v5 muscle memory. Confirm the version line is `//@version=6`.
2. **Find the source of truth.** If porting, read the Python or existing Pine end to end and match field names, constants, and thresholds exactly. Cite the constants in a header comment. Only add new behavior after the faithful port is in place, and say plainly which parts are new.
3. **Scaffold in house style.** Header comment block, palette consts, grouped inputs, calculations, draw, plots, alerts, dashboard. See the templates below.
4. **Run the v6 landmine checklist** (below) against the finished file.
5. **Scan for em dashes.** Search the file for U+2014 and U+2013, including code comments and string literals. Replace with a hyphen or comma. This is the single most common house-rule miss in generated code.
6. **Hand off for compile.** There is no offline Pine compiler. Load the finished script onto the user's clipboard and tell them to paste it into TradingView's Pine Editor, Save, Add to chart, and report any red error. Fix reported errors and reload the clipboard.
7. **Save and offer to ship.** Write to `docs/pine/<name>.pine` in the relevant repo. Offer `/ship`. Never commit without being asked.

## v6 landmine checklist

These are the v6 breaking changes and gotchas that bite when porting from v5 or from memory:

- **`bool` cannot be `na`.** Never write `var bool x = na`. Use an `int` flag (0 / 1 / -1) for tri-state. `na()`, `nz()`, `fixnan()` no longer accept bool.
- **No implicit int or float to bool cast.** Write explicit comparisons: `if count > 0`, not `if count`.
- **`and` / `or` are lazy.** Short-circuit is fine, but do not rely on side effects in the right operand.
- **Enums and `input.enum`.** Declare `enum Name` with optional `field = "Title"` strings, then `input.enum(Name.first, "Label")`. Compare with `==`. Cleaner than magic strings.
- **Dynamic `request.security`.** A single call can take a `series string` symbol or timeframe. Use `lookahead=barmerge.lookahead_off` to stay non-repainting.
- **`input.timeframe("")` off-slot trick.** An empty timeframe means the chart timeframe. For an optional higher-TF confirm, never gate `request.security` behind a ternary on the empty string (Pine evaluates both branches). Instead call `request.security` on a fallback (`htf_on ? htf_tf : timeframe.period`) and ignore the result when off.
- **`plotchar` / `plotshape` args must be const.** `char`, `text`, and `location` cannot be series. Split a direction-dependent marker into two calls with fixed `location.belowbar` / `location.abovebar`.
- **User functions must be global.** Declare every `f_*()` at top level, never inside an `if` block or a local scope.
- **Medians.** Pine has no `ta.median`. Use `ta.percentile_linear_interpolation(src, len, 50)`.
- **Pine gives you no slope or r2 directly.** Hand-roll least squares (snippet below).
- Set generous `max_bars_back`, `max_lines_count`, `max_labels_count` on `indicator()` when drawing persistent objects or looping over history.
- Heavy per-bar loops (pivot scans, multi-pass fits) can trip the execution-time limit on long intraday histories. Keep lookbacks modest and note the tradeoff.

## House style template

```pine
// <Name> [mph1nance] - <one line purpose>
// (c) mph1nance + Sam the Quant Ghost
//
// PURPOSE: <what it does and why it beats the generic version>
// Faithful port of <source>. Constants: <list them>.

//@version=6
indicator("<Name> [mph1nance]", "<glyph>", overlay=true, max_bars_back=600, max_lines_count=30, max_labels_count=50)

// Synthwave palette (reuse these names)
const color C_BULL    = #00FFFF
const color C_BEAR    = #FF00FF
const color C_NEUTRAL = #9C27B0
const color C_BREAK   = #FF3D00
const color C_CONF    = #00FFCC
const color C_WARN    = #FFD740
const color C_BG      = #090014
const color C_BORDER  = #FF00FF
const color C_TEXT    = #00FFFF

// Grouped inputs
g_main = "--- Main ---"
// ... input.int / input.float / input.enum, all with group=g_main
```

### Dashboard scaffold plus AI payload row

Build the table once on `barstate.isfirst`, fill it on `barstate.islast`. Left column is the label, right column is the value, color carries meaning. End with a single compressed pipe-delimited row that an OCR or screenshot reader can parse.

```pine
var table tbl = na
if barstate.isfirst and show_tbl
    tbl := table.new(tbl_pos, 2, 16, bgcolor=C_BG, border_width=2, border_color=C_BORDER, frame_width=3, frame_color=C_BORDER)
if barstate.islast and show_tbl
    int row = 0
    table.cell(tbl, 0, row, "<TITLE>", text_color=C_TEXT, text_halign=text.align_center, bgcolor=color.new(C_BORDER, 70))
    table.merge_cells(tbl, 0, row, 1, row)
    row += 1
    // ... one row per metric, color-coded ...
    // Final AI payload row, merged across both columns:
    string ai = syminfo.ticker + "|" + timeframe.period + "|" + verdict + "|" + str.tostring(value)
    table.cell(tbl, 0, row, ai, text_color=color.new(C_TEXT, 75), text_size=size.tiny, text_halign=text.align_center)
    table.merge_cells(tbl, 0, row, 1, row)
```

### Alerts pattern

Pair static `alertcondition` calls (one per discrete event) with a single dynamic `alert()` on bar close that carries the full context string.

```pine
alertcondition(brk_above, "Breakout up", "Price broke above")
if barstate.isconfirmed and (brk_above or brk_below)
    alert(syminfo.ticker + " " + timeframe.period + " | " + verdict + " | " + str.tostring(score), alert.freq_once_per_bar_close)
```

## Reusable math snippets

### Least squares: slope, intercept, r2

Array index convention: a = 0 is the oldest bar in the window, a = len-1 is the latest. The series offset for index a is `src[(len-1)-a]`.

```pine
f_linreg(float src, int len) =>
    float n = len, sx = 0.0, sy = 0.0, sxx = 0.0, sxy = 0.0, syy = 0.0
    for i = 0 to len - 1
        float xi = i, yi = src[(len - 1) - i]
        sx += xi
        sy += yi
        sxx += xi * xi
        sxy += xi * yi
        syy += yi * yi
    float denx = n * sxx - sx * sx
    float deny = n * syy - sy * sy
    float slope = denx == 0.0 ? 0.0 : (n * sxy - sx * sy) / denx
    float icept = (sy - slope * sx) / n
    float r2 = (denx == 0.0 or deny == 0.0) ? 0.0 : math.max(0.0, math.min(1.0, math.pow(n * sxy - sx * sy, 2) / (denx * deny)))
    [slope, icept, r2]
```

Note: declare each local on its own line in real code. Pine does not accept comma-separated declarations on one line. The above is compressed for the doc only.

### Residual std (for std-dev rails)

Loop the window, accumulate `(yi - (slope*i + icept))^2`, return `sqrt(sum / len)`. Matches numpy `np.std`.

### Volume-confirm median

```pine
float vol_med = ta.percentile_linear_interpolation(volume, 20, 50)
bool vol_strong = vol_med > 0.0 and volume > 1.5 * vol_med   // VOLUME_CONFIRM_MULT
```

### Reward / risk geometry

Stop a buffer (for example 0.5 ATR) beyond the relevant level. In-channel setups target the opposite rail; breakout setups target a measured move (one channel height). Always guard `risk > 0` before dividing.

### Context-gated candlestick patterns

Detect the raw pattern, then only flag it when it prints AT a level. A hammer in open space is noise. A hammer tagging the lower rail of an ascending channel is a signal.

```pine
float body = math.abs(close - open), rng = high - low
float up = high - math.max(close, open), dn = math.min(close, open) - low
bool doji   = rng > 0.0 and body <= rng * 0.1
bool hammer = rng > 0.0 and dn >= body * 2.0 and up <= body and not doji
bool bull_eng = close > open and close[1] < open[1] and close >= open[1] and open <= close[1]
bool react_bull = tag_lower and (hammer or bull_eng)   // tag_lower = price reached the level
```

## Hard rules

- No em dashes anywhere, including code comments and string literals. Scan for U+2014 and U+2013 before delivering. Replace with a hyphen or comma.
- No markdown tables in any prose meant for Substack. This rule is about deliverables, not this skill file.
- Faithful before fancy. If porting an engine, match its field names and constants exactly first. Label every addition as new.
- Never invent indicator behavior the user did not ask for. Propose, then build.
- There is no offline Pine compiler. Always verify by clipboard handoff to TradingView, never claim it compiles from inspection alone.
- Write the script to `docs/pine/<name>.pine`. Surface the absolute path. Offer `/ship`, never auto-commit.

## Out of scope

- Auto-compiling or auto-deploying scripts. TradingView is the only compiler and the user drives it.
- Placing trades or wiring live orders. Indicators are advisory.
- Anything not described above. If the user wants something adjacent, ask before extending the skill.
