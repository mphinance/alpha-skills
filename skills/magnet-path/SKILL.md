---
name: magnet-path
description: >-
  Render a "Magnet Path" chart for a ticker — past price history on the left,
  then a forward projection of option gamma pins (magnets) across future
  expiries on the right, with the gamma-flip trajectory overlaid. Bubble size =
  pin open interest, green = positive gamma, red = negative gamma. Use when the
  user asks for a "magnet path", "gamma pins chart", "price vs the pins", "apex
  evolution chart", "where do the pins pull price", or wants the forward-looking
  gamma view for a symbol.
---

# magnet-path

Forward-looking companion to a GEX snapshot. Where a gamma-wall chart shows the
pins for *today*, this projects the magnet (the strike price pulls toward) across
the next several expiries, so you can see the path price is being pulled along.

## Run

```
python scripts/magnet_path.py SYMBOL [--out path.png] [--days 30] [--max-expiries 5]
```

- `--days` — days of price history on the left (default 30)
- `--max-expiries` — forward expiries to plot (default 5)
- `--out` — output PNG path (default `<symbol>_magnet.png`)

Prints the output path on success.

## Data

TraderDaddy Pro agent API. Auth token is the raw single-line contents of
`.env_agent_api` (walks up from CWD to the mphinance repo, or `MPHINANCE_ROOT`,
else `/home/mph/mphinance/.env_agent_api`). Requires a browser `User-Agent`.

- Price line: `/api/agent/ticker/{SYM}/chart-data?days=N`
- Forward pins: `/api/agent/gex/{SYM}/apex/evolution?maxExpiries=M`
  → `spot`, `gammaFlipTrajectory[]`, `rows[{date, dte, magnet, regime, magnetOI}]`

## How to read it

- **Magnet** (green/red bubble) = the strike price gets pulled toward at that
  expiry. Bubble size and glow scale with open interest = how much conviction
  sits on that pin.
- **Green** = positive gamma regime (dealers dampen moves, price gets pinned).
  **Red** = negative gamma (dealers feed the move, volatility expands).
- **Gamma flip** (orange dotted) = the price where dealers switch from long to
  short gamma. Above the flip, moves get dampened; below it, they accelerate.
- **The key read:** when the magnet lands on the gamma flip at the same expiry,
  that price is the fulcrum — the most unstable, most magnetic level for that
  week. A magnet below spot in a negative regime = downside pull.

## Example

`python scripts/magnet_path.py SLB` — SLB's path pulls up toward the $48 pin
near-term, sags to a negative-gamma $45 magnet that meets the flip on the 8/07
expiry (the re-load fulcrum), then a heavy positive $52.50 monthly magnet into
8/21 where the biggest OI sits.
