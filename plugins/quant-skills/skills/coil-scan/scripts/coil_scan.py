#!/usr/bin/env python3
"""
coil-scan — dual-timeframe Williams %R Trend Exhaustion scanner.

Mirrors the "%R Trend Exhaustion [upslidedown]" TradingView indicator:
  - Fast leg  = EMA(7) of %R(21)
  - Slow leg  = EMA(3) of %R(112)
  - Threshold = -80
  - "In the coil": both legs <= -80 (double-oversold, stalk mode)
  - "Triggered out": fast just crossed back above -80 after both were <= -80

Universe: pulled live from all TDPro screeners + persistent watch list from
stock-recap skill (falls back to union of screener_*.json in most recent run).

Data: TraderDaddy Pro Railway API (chart-data + technicals per ticker).
State: .claude/skills/coil-scan/state/coil_watch.json -- tracks "days in coil"
       across runs so Michael can see "IREN -- day 6 in the coil".

Usage:
  python3 coil_scan.py
  python3 coil_scan.py --universe /tmp/my_tickers.txt
  python3 coil_scan.py --json /tmp/out.json
  python3 coil_scan.py --limit 200
  python3 coil_scan.py --universe IREN,RGTI,SMCI,SLB,FIG,GLD,ASTS

Env:
  MPHINANCE_ROOT   override repo root (auto-detected via walk-up otherwise)
  AGENT_API_KEY    override token
"""

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TD_BASE = "https://traderdaddy-pro-whop-production.up.railway.app"
TH      = -80
BARS_DAYS            = 365
MIN_BARS             = 115
WORKERS              = 6
TRIGGER_WINDOW       = 20
FRESH_TRIGGER_MAX_DAYS = 3
ALREADY_RAN_PCT      = 5.0   # close > trigger-close by more than this % => already ran

UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

SCREENER_IDS = [
    "momentum", "bullish-pullback", "volatility-squeeze", "small-cap",
    "volatility-surge", "gamma-scan", "csp-wheel", "leaps", "leveraged",
    "daily-cuts",
]

# ---------------------------------------------------------------------------
# Path resolution
# ---------------------------------------------------------------------------

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR  = SCRIPT_DIR.parent
STATE_FILE = SKILL_DIR / "state" / "coil_watch.json"


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(8):
        if (cur / ".env_agent_api").exists() or (cur / "CLAUDE.md").exists():
            return cur
        parent = cur.parent
        if parent == cur:
            break
        cur = parent
    env = os.environ.get("MPHINANCE_ROOT")
    if env:
        return Path(env)
    return Path("/home/mph/mphinance")


REPO_ROOT = find_repo_root(SCRIPT_DIR)


def load_agent_key() -> str:
    env = os.environ.get("AGENT_API_KEY", "").strip()
    if env:
        return env
    key_file = REPO_ROOT / ".env_agent_api"
    if key_file.exists():
        raw = key_file.read_text().strip()
        if "=" in raw and raw.split("=", 1)[0].isupper():
            return raw.split("=", 1)[1].strip()
        return raw
    raise RuntimeError(f".env_agent_api not found under {REPO_ROOT}")


# ---------------------------------------------------------------------------
# Math -- Williams %R and EMA (exact reference implementation logic)
# ---------------------------------------------------------------------------

def wpr(highs, lows, closes, length):
    """Williams %R: range -100..0.  None for bars with insufficient history."""
    out = [None] * len(closes)
    for i in range(len(closes)):
        if i + 1 < length:
            continue
        hh  = max(highs[i - length + 1 : i + 1])
        ll  = min(lows[i  - length + 1 : i + 1])
        rng = hh - ll
        out[i] = 0.0 if rng == 0 else 100.0 * (closes[i] - hh) / rng
    return out


def ema(vals, length):
    """EMA seeded with first non-None value, k = 2/(length+1)."""
    out  = [None] * len(vals)
    k    = 2.0 / (length + 1)
    prev = None
    for i, v in enumerate(vals):
        if v is None:
            continue
        prev   = v if prev is None else v * k + prev * (1 - k)
        out[i] = prev
    return out


def compute_rte(bars):
    """
    Dual-timeframe %R Trend Exhaustion.
    fast = EMA(7)  of %R(21)
    slow = EMA(3)  of %R(112)
    Returns (dates, fast_series, slow_series).
    """
    h = [b["h"] for b in bars]
    l = [b["l"] for b in bars]
    c = [b["c"] for b in bars]
    d = [b["d"] for b in bars]
    fast = ema(wpr(h, l, c,  21),  7)
    slow = ema(wpr(h, l, c, 112),  3)
    return d, fast, slow


# ---------------------------------------------------------------------------
# Trigger detection
# ---------------------------------------------------------------------------

def find_trigger(fast, slow, lookback=TRIGGER_WINDOW):
    """
    Look back `lookback` bars for the most recent oversold->reversal cross.
    Both legs must have been <= TH, then fast crosses back above TH.
    Returns (bars_ago, bar_index) or (None, None).
    """
    i         = len(fast) - 1
    trig_days = None
    trig_idx  = None
    was_os    = False
    for j in range(max(0, i - lookback), i + 1):
        f = fast[j]
        s = slow[j]
        if f is None or s is None:
            continue
        if f <= TH and s <= TH:
            was_os = True
        elif was_os and f > TH:
            trig_days = i - j
            trig_idx  = j
            was_os    = False   # keep scanning to find the LATEST trigger
    return trig_days, trig_idx


# ---------------------------------------------------------------------------
# Per-ticker analysis
# ---------------------------------------------------------------------------

def analyze_ticker(symbol, bars, tech):
    if len(bars) < MIN_BARS:
        return None

    dates, fast, slow = compute_rte(bars)
    i = len(bars) - 1
    f = fast[i]
    s = slow[i]
    if f is None or s is None:
        return None

    in_coil              = f <= TH and s <= TH
    trig_days, trig_idx  = find_trigger(fast, slow)

    already_ran = False
    run_pct     = None
    if trig_days is not None and trig_idx is not None:
        close_now     = bars[i]["c"]
        close_trigger = bars[trig_idx]["c"]
        if close_trigger > 0:
            run_pct = (close_now - close_trigger) / close_trigger * 100.0
        ema21_now  = (tech or {}).get("ema21")
        above_e21  = ema21_now is not None and close_now > ema21_now
        if (run_pct is not None and run_pct > ALREADY_RAN_PCT) or above_e21:
            already_ran = True

    close   = bars[i]["c"]
    sma200  = (tech or {}).get("sma200")
    ema21   = (tech or {}).get("ema21")

    return {
        "symbol":       symbol,
        "fast":         round(f, 1),
        "slow":         round(s, 1),
        "depth":        round(min(f, s) - TH, 1),
        "in_coil":      in_coil,
        "trig_days":    trig_days,
        "trig_idx":     trig_idx,
        "already_ran":  already_ran,
        "run_pct":      round(run_pct, 1) if run_pct is not None else None,
        "close":        close,
        "last_date":    dates[i],
        "above_sma200": sma200 is not None and close > sma200,
        "above_ema21":  ema21  is not None and close > ema21,
        "ema21":        ema21,
        "sma200":       sma200,
    }


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def get_json(url, token, retries=1):
    headers = {
        "Authorization": f"Bearer {token}",
        "User-Agent":    UA,
        "Accept":        "application/json",
    }
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            if e.code == 502 and attempt < retries:
                time.sleep(1)
                continue
            return None
        except Exception:
            return None
    return None


def fetch_bars(symbol, token):
    """
    Fetch OHLC bars from the chart-data endpoint.

    Actual API response shape:
      {
        "ticker": "IREN",
        "chartData": [{"date","open","high","low","close","ema21","sma200",...}, ...],
        "latestMetrics": {"ema21":..., "sma200":..., ...},
        ...
      }

    Returns (bars_list_or_None, latestMetrics_dict).
    bars_list is None if fewer than MIN_BARS valid rows were parsed.
    """
    url  = f"{TD_BASE}/api/agent/ticker/{urllib.parse.quote(symbol)}/chart-data?days={BARS_DAYS}"
    data = get_json(url, token)
    if not data:
        return None, {}

    if isinstance(data, dict):
        rows   = (data.get("chartData") or data.get("bars")
                  or data.get("data") or [])
        latest = data.get("latestMetrics") or {}
    else:
        rows   = data
        latest = {}

    out = []
    for r in rows:
        # prefer long field names (date/open/high/low/close), fall back to short
        d = r.get("date")  or r.get("d") or r.get("t") or ""
        o = r.get("open")  or r.get("o") or 0.0
        h = r.get("high")  or r.get("h") or 0.0
        l = r.get("low")   or r.get("l") or 0.0
        c = r.get("close") or r.get("c") or 0.0
        try:
            h_f, l_f, c_f = float(h), float(l), float(c)
            if h_f > 0:
                out.append({"d": str(d), "o": float(o),
                            "h": h_f, "l": l_f, "c": c_f})
        except (TypeError, ValueError):
            pass

    return (out if len(out) >= MIN_BARS else None), latest


def fetch_technicals(symbol, token, cached_latest=None):
    """
    Extract ema21/sma200/rsi etc.
    Reuses latestMetrics already returned from the chart-data call when provided.
    Falls back to a dedicated single-ticker GET if not.
    """
    if cached_latest:
        tech = cached_latest
    else:
        url  = f"{TD_BASE}/api/agent/ticker/{urllib.parse.quote(symbol)}"
        data = get_json(url, token)
        if not data:
            return {}
        tech = (data.get("technicals") or data.get("latestMetrics") or data)

    return {k: tech.get(k) for k in
            ("close", "ema21", "sma200", "atr", "rsi", "williamsR")}


# ---------------------------------------------------------------------------
# Universe
# ---------------------------------------------------------------------------

def fetch_screener_universe(token):
    tickers   = set()
    list_data = get_json(f"{TD_BASE}/api/screeners", token)
    if list_data and list_data.get("screeners"):
        ids = [s["id"] for s in list_data["screeners"]]
    else:
        ids = SCREENER_IDS

    def run_screener(sid):
        data = get_json(f"{TD_BASE}/api/screeners/{urllib.parse.quote(sid)}/run", token)
        if not data:
            return []
        rows = data if isinstance(data, list) else (
            data.get("results") or data.get("data") or data.get("rows") or []
        )
        out = []
        for r in rows:
            sym = (r.get("symbol") or r.get("ticker")
                   or r.get("Symbol") or "").upper().strip()
            if sym:
                out.append(sym)
        return out

    with ThreadPoolExecutor(max_workers=4) as ex:
        futures = {ex.submit(run_screener, sid): sid for sid in ids}
        for fut in as_completed(futures):
            for sym in fut.result():
                tickers.add(sym)

    return tickers


def load_watchlist_tickers():
    watch_path = SKILL_DIR.parent / "stock-recap" / "runs" / "_watchlist.json"
    if watch_path.exists():
        try:
            data = json.loads(watch_path.read_text())
            return set((data.get("names") or {}).keys())
        except Exception:
            pass
    return set()


def load_fallback_universe():
    """Union all tickers from the most recent stock-recap run's screener_*.json."""
    runs_dir = SKILL_DIR.parent / "stock-recap" / "runs"
    tickers  = set()
    if not runs_dir.exists():
        return tickers
    run_dirs = sorted(
        [d for d in runs_dir.iterdir()
         if d.is_dir() and d.name[:4].isdigit()],
        reverse=True,
    )
    if not run_dirs:
        return tickers
    raw_dir = run_dirs[0] / "raw"
    if not raw_dir.exists():
        return tickers
    for f in raw_dir.glob("screener_*.json"):
        try:
            data = json.loads(f.read_text())
            rows = data if isinstance(data, list) else (
                data.get("results") or data.get("data") or data.get("rows") or []
            )
            for r in rows:
                sym = (r.get("symbol") or r.get("ticker") or "").upper().strip()
                if sym:
                    tickers.add(sym)
        except Exception:
            pass
    return tickers


def build_universe(args_universe, token):
    if args_universe:
        u = args_universe.strip()
        # comma list OR all-caps ticker string with no path separator
        if "," in u or (not os.path.exists(u) and u == u.upper()):
            return sorted({t.strip().upper() for t in u.split(",") if t.strip()})
        p = Path(u)
        if p.exists():
            tickers = set()
            for line in p.read_text().splitlines():
                for t in line.split(","):
                    t = t.strip().upper()
                    if t:
                        tickers.add(t)
            return sorted(tickers)

    print("[universe] pulling live screener universe...", file=sys.stderr)
    tickers = fetch_screener_universe(token)
    print(f"[universe] {len(tickers)} from live screeners", file=sys.stderr)

    watch = load_watchlist_tickers()
    if watch:
        print(f"[universe] +{len(watch)} from stock-recap watch list", file=sys.stderr)
        tickers |= watch

    if len(tickers) < 20:
        print("[universe] live screeners sparse -- loading fallback from runs/",
              file=sys.stderr)
        tickers |= load_fallback_universe()

    return sorted(tickers)


# ---------------------------------------------------------------------------
# Coil watch state
# ---------------------------------------------------------------------------

TODAY = date.today().isoformat()


def load_coil_watch():
    if STATE_FILE.exists():
        try:
            data = json.loads(STATE_FILE.read_text())
            if isinstance(data, dict) and "names" in data:
                return data
        except Exception:
            pass
    return {"version": 1, "updated": None, "names": {}}


def save_coil_watch(store):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    store["updated"] = TODAY
    STATE_FILE.write_text(json.dumps(store, indent=2))


def days_between(a: str, b: str) -> int:
    try:
        return (date.fromisoformat(b) - date.fromisoformat(a)).days
    except Exception:
        return 0


def update_coil_watch(store, results):
    """
    - Names currently in the coil: add/update with days-in-coil counter.
    - Names that just triggered (fresh): mark triggered.
    - Everything else: drop.
    """
    seen = set()

    for r in results:
        if r is None:
            continue
        sym = r["symbol"]
        rec = store["names"].get(sym)

        if r["in_coil"]:
            seen.add(sym)
            if rec:
                rec["lastSeen"]   = TODAY
                rec["lastClose"]  = r["close"]
                rec["daysInCoil"] = days_between(rec["firstSeen"], TODAY)
                rec["fastR"]      = r["fast"]
                rec["slowR"]      = r["slow"]
                rec["depth"]      = r["depth"]
            else:
                store["names"][sym] = {
                    "firstSeen":   TODAY,
                    "lastSeen":    TODAY,
                    "entryClose":  r["close"],
                    "lastClose":   r["close"],
                    "daysInCoil":  0,
                    "fastR":       r["fast"],
                    "slowR":       r["slow"],
                    "depth":       r["depth"],
                    "triggered":   False,
                    "triggerDate": None,
                }

        elif (r["trig_days"] is not None
              and r["trig_days"] <= FRESH_TRIGGER_MAX_DAYS):
            seen.add(sym)
            if rec:
                rec["triggered"]   = True
                rec["triggerDate"] = TODAY
                rec["lastClose"]   = r["close"]
            else:
                store["names"][sym] = {
                    "firstSeen":   TODAY,
                    "lastSeen":    TODAY,
                    "entryClose":  r["close"],
                    "lastClose":   r["close"],
                    "daysInCoil":  0,
                    "fastR":       r["fast"],
                    "slowR":       r["slow"],
                    "depth":       r["depth"],
                    "triggered":   True,
                    "triggerDate": TODAY,
                }

    # drop names that are no longer coiled or freshly triggered
    for k in [k for k in store["names"] if k not in seen]:
        del store["names"][k]

    return store


# ---------------------------------------------------------------------------
# Main scan
# ---------------------------------------------------------------------------

def run_scan(universe, token, limit=None):
    if limit:
        universe = universe[:limit]

    total = len(universe)
    print(f"[scan] {total} tickers, {WORKERS} workers...", file=sys.stderr)

    def fetch_one(sym):
        bars, latest = fetch_bars(sym, token)
        tech = fetch_technicals(sym, token, cached_latest=latest) if bars else {}
        return sym, bars, tech

    results = []
    done    = 0
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(fetch_one, sym): sym for sym in universe}
        for fut in as_completed(futures):
            sym, bars, tech = fut.result()
            done += 1
            if done % 20 == 0 or done == total:
                print(f"[scan] {done}/{total}", file=sys.stderr)
            if bars is None:
                continue
            result = analyze_ticker(sym, bars, tech)
            if result:
                results.append(result)

    return results


# ---------------------------------------------------------------------------
# Display
# ---------------------------------------------------------------------------

def vs(above: bool, label: str) -> str:
    return f"above {label}" if above else f"below {label}"


def print_report(in_coil, triggered, watch_names):
    fresh = [r for r in triggered if not r["already_ran"]]
    stale = [r for r in triggered if r["already_ran"]]

    print(f"\n{'='*68}")
    print(f"  COIL SCAN  --  {TODAY}")
    print(f"{'='*68}")

    print(f"\n[TRIGGERED OUT]  fast crossed back above -80  (<= {FRESH_TRIGGER_MAX_DAYS}d ago)\n")

    if fresh:
        for r in fresh:
            sym   = r["symbol"]
            rec   = watch_names.get(sym, {})
            d_in  = rec.get("daysInCoil", 0)
            d_ago = r["trig_days"]
            s200  = vs(r["above_sma200"], "SMA200")
            e21   = vs(r["above_ema21"],  "EMA21")
            coil_l = f"  (was in coil {d_in}d)" if d_in > 0 else ""
            print(f"  {sym:<6}  fast {r['fast']:>7}  slow {r['slow']:>7}  "
                  f"close ${r['close']:.2f}  trig {d_ago}d ago  "
                  f"{s200}  {e21}{coil_l}")
    else:
        print("  (none)")

    if stale:
        print(f"\n  -- sanity-filtered (already ran, not fresh) --")
        for r in stale:
            note = (f"+{r['run_pct']:.1f}% from trigger"
                    if r["run_pct"] else "above EMA21")
            e21  = vs(r["above_ema21"], "EMA21")
            print(f"  {r['symbol']:<6}  fast {r['fast']:>7}  slow {r['slow']:>7}  "
                  f"close ${r['close']:.2f}  trig {r['trig_days']}d ago  "
                  f"{e21}  [{note} -- already ran]")

    print(f"\n{'─'*68}")
    print(f"\n[IN THE COIL]  both fast + slow <= -80  --  stalk candidates\n")
    print(f"  {'SYM':<6}  {'fast%R':>7}  {'slow%R':>7}  {'depth':>6}  "
          f"{'close':>7}  day-in-coil")
    print(f"  {'─'*6}  {'─'*7}  {'─'*7}  {'─'*6}  {'─'*7}  {'─'*11}")

    if in_coil:
        for r in in_coil:
            sym   = r["symbol"]
            rec   = watch_names.get(sym, {})
            d_in  = rec.get("daysInCoil", 0)
            s200  = vs(r["above_sma200"], "SMA200")
            e21   = vs(r["above_ema21"],  "EMA21")
            d_lab = f"day {d_in}" if d_in > 0 else "new"
            print(f"  {sym:<6}  {r['fast']:>7}  {r['slow']:>7}  {r['depth']:>6}  "
                  f"${r['close']:>6.2f}  {d_lab:<11}  {s200}  {e21}")
    else:
        print("  (none in coil this run)")

    print(f"\n{'='*68}\n")


# ---------------------------------------------------------------------------
# JSON output
# ---------------------------------------------------------------------------

def build_output(in_coil, triggered, watch_names):
    def enrich(r):
        rec = watch_names.get(r["symbol"], {})
        return {**r, "daysInCoil": rec.get("daysInCoil", 0)}

    fresh = [r for r in triggered if not r["already_ran"]]
    stale = [r for r in triggered if r["already_ran"]]
    return {
        "date":                  TODAY,
        "generated":             datetime.now().isoformat() + "Z",
        "in_coil":               [enrich(r) for r in in_coil],
        "triggered_fresh":       [enrich(r) for r in fresh],
        "triggered_already_ran": [enrich(r) for r in stale],
        "counts": {
            "in_coil":               len(in_coil),
            "triggered_fresh":       len(fresh),
            "triggered_already_ran": len(stale),
        },
    }


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(
        description="Williams %R Trend Exhaustion coil scanner")
    ap.add_argument(
        "--universe", default=None,
        help=("Comma-separated tickers, or path to file, "
              "or omit for live screeners"))
    ap.add_argument(
        "--json", default=None, dest="json_out",
        help="Write JSON output to this path")
    ap.add_argument(
        "--limit", type=int, default=None,
        help="Cap universe size (useful for smoke tests)")
    args = ap.parse_args()

    token    = load_agent_key()
    universe = build_universe(args.universe, token)

    if not universe:
        print("ERROR: universe is empty", file=sys.stderr)
        sys.exit(1)

    print(f"[coil-scan] universe: {len(universe)} tickers", file=sys.stderr)
    results = run_scan(universe, token, limit=args.limit)

    in_coil = sorted(
        [r for r in results if r["in_coil"]],
        key=lambda r: r["slow"],
    )
    triggered = sorted(
        [r for r in results
         if not r["in_coil"]
         and r["trig_days"] is not None
         and r["trig_days"] <= FRESH_TRIGGER_MAX_DAYS],
        key=lambda r: (1 if r["already_ran"] else 0, r["trig_days"]),
    )

    store = load_coil_watch()
    update_coil_watch(store, results)
    save_coil_watch(store)

    print_report(in_coil, triggered, store["names"])

    payload = build_output(in_coil, triggered, store["names"])

    if args.json_out:
        out = Path(args.json_out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2))
        print(f"[coil-scan] JSON -> {out}", file=sys.stderr)

    runs_dir = SKILL_DIR / "runs"
    runs_dir.mkdir(exist_ok=True)
    run_file = runs_dir / f"{TODAY}.json"
    run_file.write_text(json.dumps(payload, indent=2))
    print(f"[coil-scan] run -> {run_file}", file=sys.stderr)


if __name__ == "__main__":
    main()
