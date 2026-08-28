#!/usr/bin/env python3
"""
magnet-path — render a "Magnet Path" chart: past price history on the left,
then a forward projection of option gamma pins (magnets) across future
expiries on the right, with the gamma-flip trajectory overlaid.

Data: TraderDaddy Pro agent API.
  price history : /api/agent/ticker/{SYM}/chart-data?days=N   -> chartData[{date,close,...}]
  forward pins  : /api/agent/gex/{SYM}/apex/evolution?maxExpiries=M
                    -> data{spot, gammaFlipTrajectory[], rows[{date,dte,magnet,regime,magnetOI}]}

Usage:
  python magnet_path.py SYMBOL [--out path.png] [--days 30] [--max-expiries 5]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

BASE = "https://traderdaddy-pro-whop-production.up.railway.app"

# HUD palette (mirrors TraderDiscord charts.py)
HUD_BG = "#0d0f12"
HUD_PANEL = "#14171c"
HUD_GRID = "#1e2329"
HUD_TEXT = "#9ba1a6"
NEON_CYAN = "#00e5ff"
NEON_LIME = "#7cff6b"
NEON_RED = "#ff4d4d"
NEON_AMBER = "#ffb020"


def _find_token() -> str:
    # Walk up from CWD looking for the mphinance repo, else env, else fallback.
    d = os.getcwd()
    for _ in range(8):
        p = os.path.join(d, ".env_agent_api")
        if os.path.isfile(p):
            return open(p).read().strip()
        nd = os.path.dirname(d)
        if nd == d:
            break
        d = nd
    root = os.environ.get("MPHINANCE_ROOT", "/home/mph/mphinance")
    p = os.path.join(root, ".env_agent_api")
    if os.path.isfile(p):
        return open(p).read().strip()
    sys.exit("magnet_path: could not locate .env_agent_api")


def _get(path: str, token: str) -> dict:
    req = urllib.request.Request(
        BASE + path,
        headers={"Authorization": f"Bearer {token}", "User-Agent": "Mozilla/5.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode())


def render(sym: str, out: str, days: int, max_expiries: int) -> str:
    token = _find_token()
    sym = sym.upper()

    hist = _get(f"/api/agent/ticker/{sym}/chart-data?days={days}", token)
    bars = hist.get("chartData", [])
    if not bars:
        sys.exit(f"magnet_path: no price history for {sym}")
    px_dates = [datetime.strptime(b["date"], "%Y-%m-%d") for b in bars]
    px_close = [float(b["close"]) for b in bars]
    spot = float(hist.get("currentPrice") or px_close[-1])

    evo = _get(f"/api/agent/gex/{sym}/apex/evolution?maxExpiries={max_expiries}", token)
    data = evo.get("data", {})
    rows = data.get("rows", [])
    flips = data.get("gammaFlipTrajectory", [])
    spot = float(data.get("spot") or spot)
    if not rows:
        sys.exit(f"magnet_path: no apex evolution rows for {sym}")

    exp_dates = [datetime.strptime(r["date"], "%Y-%m-%d") for r in rows]
    magnets = [float(r["magnet"]) for r in rows]
    ois = [float(r.get("magnetOI") or 0) for r in rows]
    regimes = [r.get("regime", "positive") for r in rows]
    dtes = [r.get("dte") for r in rows]

    fig, ax = plt.subplots(figsize=(9.4, 5.2))
    fig.patch.set_facecolor(HUD_BG)
    ax.set_facecolor(HUD_PANEL)

    # ---- price history line + glow ----
    xh = mdates.date2num(px_dates)
    ax.plot(xh, px_close, color=NEON_CYAN, lw=1.8, zorder=4)
    ax.plot(xh, px_close, color=NEON_CYAN, lw=5.0, alpha=0.15, zorder=3)
    ax.annotate(f"Spot ${spot:,.0f}", (xh[-1], px_close[-1]), color=NEON_CYAN,
                fontsize=10, fontweight="bold", xytext=(6, -14),
                textcoords="offset points", zorder=6)

    # ---- "now" divider ----
    now_x = xh[-1]
    ax.axvline(now_x, color=HUD_TEXT, lw=0.8, ls="--", alpha=0.5, zorder=2)

    # ---- forward magnets ----
    xe = mdates.date2num(exp_dates)
    ax.plot(xe, magnets, color="#4a525b", lw=1.4, zorder=4)
    maxoi = max(ois) or 1.0
    for x, m, oi, reg in zip(xe, magnets, ois, regimes):
        size = 120 + 900 * (oi / maxoi)
        col = NEON_LIME if reg == "positive" else NEON_RED
        ax.scatter([x], [m], s=size * 1.6, color=col, alpha=0.16, zorder=5)
        ax.scatter([x], [m], s=size, color=col, edgecolors=HUD_BG, lw=1.2, zorder=6)
        ax.annotate(f"${m:,.0f}", (x, m), color=col, fontsize=10, fontweight="bold",
                    xytext=(0, 12), textcoords="offset points", ha="center", zorder=7)

    # ---- gamma flip trajectory ----
    fx, fy = [], []
    for x, fv in zip(xe, flips):
        if fv is not None:
            fx.append(x); fy.append(float(fv))
    if fx:
        ax.plot(fx, fy, color=NEON_AMBER, lw=1.3, ls=":", marker="D",
                markersize=6, zorder=5, label="Gamma flip")

    # ---- DTE labels under the expiries ----
    ymin = min(min(px_close), min(magnets), *(fy or [min(magnets)]))
    ymax = max(max(px_close), max(magnets), *(fy or [max(magnets)]))
    pad = (ymax - ymin) * 0.12
    ax.set_ylim(ymin - pad * 1.4, ymax + pad)
    for x, dte in zip(xe, dtes):
        if dte is not None:
            ax.annotate(f"{dte}d", (x, ymin - pad * 1.15), color=HUD_TEXT, fontsize=8,
                        ha="center", zorder=5)

    # ---- legend proxies ----
    from matplotlib.lines import Line2D
    handles = [
        Line2D([0], [0], color=NEON_CYAN, lw=2, label="Price"),
        Line2D([0], [0], marker="o", color=HUD_BG, markerfacecolor=NEON_LIME,
               markersize=9, lw=0, label="Positive gamma"),
        Line2D([0], [0], marker="o", color=HUD_BG, markerfacecolor=NEON_RED,
               markersize=9, lw=0, label="Negative gamma"),
        Line2D([0], [0], color=NEON_AMBER, lw=1.5, ls=":", marker="D",
               markersize=6, label="Gamma flip"),
    ]
    leg = ax.legend(handles=handles, loc="upper left", facecolor=HUD_PANEL,
                    edgecolor=HUD_GRID, fontsize=8, framealpha=0.9)
    for t in leg.get_texts():
        t.set_color(HUD_TEXT)

    ax.set_title(f"{sym}  Magnet Path — price vs the pins", loc="left",
                 color=NEON_CYAN, fontsize=14, fontweight="bold", pad=18)
    ax.text(0.0, 1.015, "bubble size + glow = pin OI", transform=ax.transAxes,
            color=HUD_TEXT, fontsize=9)

    ax.text(0.30, -0.10, "\u2190 price history", transform=ax.transAxes,
            color=HUD_TEXT, fontsize=9, ha="center")
    ax.text(0.72, -0.10, "expiries \u2192", transform=ax.transAxes,
            color=HUD_TEXT, fontsize=9, ha="center")

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))
    ax.xaxis.set_major_locator(mdates.AutoDateLocator(maxticks=9))
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("bottom", "left"):
        ax.spines[s].set_color(HUD_GRID)
    ax.tick_params(colors=HUD_TEXT, labelsize=8)
    ax.grid(True, color=HUD_GRID, lw=0.5, alpha=0.6)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"${v:,.0f}"))

    fig.tight_layout()
    fig.savefig(out, facecolor=HUD_BG, dpi=130, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("symbol")
    ap.add_argument("--out", default=None)
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--max-expiries", type=int, default=5)
    a = ap.parse_args()
    out = a.out or f"{a.symbol.lower()}_magnet.png"
    path = render(a.symbol, out, a.days, a.max_expiries)
    print(path)


if __name__ == "__main__":
    main()
