#!/usr/bin/env python3
"""
coil_ab.py -- live A/B harness for two %R Trend Exhaustion trigger rules.

Reuses coil_scan.py's data + math.  Two trigger definitions:

  CURRENT  (coil_scan.find_trigger):
      both legs were <= -80 in the window, then fast crosses > -80.
      Does NOT require slow to still be under -80 at the cross.

  STRICT   (Michael's note, 2026-07-21):
      fast crosses > -80 WHILE slow is STILL <= -80 at that same bar.
      A subset of CURRENT.

Backtest (2026-07-21, 132 names) said STRICT is WORSE: the crosses it drops
(slow already recovered) outperformed at every horizon.  This harness runs
BOTH live, day by day, and accumulates realized forward returns so we can
confirm that finding over a few weeks instead of trusting one backtest.

Modes:
  python3 coil_ab.py            # scan, log today's fresh triggers to ledger
  python3 coil_ab.py --report   # re-price all logged triggers, print A/B
  python3 coil_ab.py --universe IREN,ACHR,GLD   # smoke test the log step

Ledger: state/ab_ledger.json  (deduped per distinct trigger event).
"""

import argparse
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import coil_scan as cs

LEDGER = cs.SKILL_DIR / "state" / "ab_ledger.json"
HORIZONS = [3, 5, 10, 20]


# --- strict trigger: fast breaks > TH while slow STILL <= TH at the cross ----
def find_trigger_strict(fast, slow, lookback=cs.TRIGGER_WINDOW):
    i = len(fast) - 1
    td = ti = None
    was = False
    for j in range(max(0, i - lookback), i + 1):
        f, s = fast[j], slow[j]
        if f is None or s is None:
            continue
        if f <= cs.TH and s <= cs.TH:
            was = True
        elif was and f > cs.TH and s <= cs.TH:
            td, ti, was = i - j, j, False
    return td, ti


# --- ledger io ---------------------------------------------------------------
def load_ledger():
    if LEDGER.exists():
        try:
            d = json.loads(LEDGER.read_text())
            if isinstance(d, dict) and "events" in d:
                return d
        except Exception:
            pass
    return {"version": 1, "updated": None, "events": {}}


def save_ledger(led):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    led["updated"] = cs.TODAY
    LEDGER.write_text(json.dumps(led, indent=2))


# --- fetch helper ------------------------------------------------------------
def fetch_all(universe, token):
    def one(sym):
        b, _ = cs.fetch_bars(sym, token)
        return sym, b
    out = {}
    with ThreadPoolExecutor(max_workers=cs.WORKERS) as ex:
        futs = {ex.submit(one, s): s for s in universe}
        for fut in as_completed(futs):
            sym, bars = fut.result()
            if bars and len(bars) >= cs.MIN_BARS:
                out[sym] = bars
    return out


# --- log mode: record today's fresh triggers under both rules ----------------
def do_log(universe, token):
    bars_by = fetch_all(universe, token)
    led = load_ledger()
    new_events = 0

    for sym, bars in bars_by.items():
        _, fast, slow = cs.compute_rte(bars)
        cd, ci = cs.find_trigger(fast, slow)          # current
        sd, si = find_trigger_strict(fast, slow)      # strict
        if cd is None or cd > cs.FRESH_TRIGGER_MAX_DAYS:
            continue
        trig_date = bars[ci]["d"]
        trig_close = bars[ci]["c"]
        is_strict = si is not None and si == ci
        key = f"{sym}|{trig_date}"
        if key not in led["events"]:
            led["events"][key] = {
                "symbol": sym,
                "trig_date": trig_date,
                "trig_close": trig_close,
                "strict": is_strict,
                "first_logged": cs.TODAY,
            }
            new_events += 1

    save_ledger(led)
    total = len(led["events"])
    strict_n = sum(1 for e in led["events"].values() if e["strict"])
    print(f"[coil-ab] logged {new_events} new trigger events "
          f"({total} total in ledger, {strict_n} strict)", file=sys.stderr)
    print(f"[coil-ab] ledger -> {LEDGER}", file=sys.stderr)


# --- report mode: re-price logged triggers, compute forward returns ----------
def do_report(token):
    led = load_ledger()
    events = list(led["events"].values())
    if not events:
        print("ledger empty -- run without --report first to log triggers",
              file=sys.stderr)
        return

    syms = sorted({e["symbol"] for e in events})
    bars_by = fetch_all(syms, token)

    buckets = {"strict": {h: [] for h in HORIZONS},
               "curonly": {h: [] for h in HORIZONS}}

    for e in events:
        bars = bars_by.get(e["symbol"])
        if not bars:
            continue
        dates = [b["d"] for b in bars]
        try:
            idx = dates.index(e["trig_date"])
        except ValueError:
            continue
        c0 = e["trig_close"] or bars[idx]["c"]
        if c0 <= 0:
            continue
        b = "strict" if e["strict"] else "curonly"
        for h in HORIZONS:
            if idx + h < len(bars):
                r = (bars[idx + h]["c"] - c0) / c0 * 100
                buckets[b][h].append(r)

    def agg(rr):
        if not rr:
            return "n=0"
        n = len(rr)
        avg = sum(rr) / n
        win = sum(1 for x in rr if x > 0) / n * 100
        return f"n={n:<3} avg {avg:+5.2f}%  win {win:4.1f}%"

    n_strict = sum(1 for e in events if e["strict"])
    n_cur = len(events)
    print("\n" + "=" * 74)
    print(f"  COIL A/B LIVE LEDGER  --  {cs.TODAY}")
    print(f"  {n_cur} trigger events logged since {min(e['first_logged'] for e in events)}")
    print(f"  strict={n_strict}  current-only(dropped by strict)={n_cur - n_strict}")
    print("=" * 74)
    print(f"  {'horizon':<9}{'STRICT (fast breaks, slow under)':<38}{'CURRENT-ONLY (slow recovered)':<30}")
    for h in HORIZONS:
        print(f"  {str(h)+'d':<9}{agg(buckets['strict'][h]):<38}{agg(buckets['curonly'][h]):<30}")
    print("=" * 74)
    print(f"  If CURRENT-ONLY keeps beating STRICT, the backtest holds:")
    print(f"  don't tighten the trigger to 'slow still under'.")
    print("=" * 74)


def main():
    ap = argparse.ArgumentParser(description="Live A/B for %R exhaustion triggers")
    ap.add_argument("--report", action="store_true", help="print accumulated A/B")
    ap.add_argument("--universe", default=None)
    args = ap.parse_args()

    token = cs.load_agent_key()
    if args.report:
        do_report(token)
        return

    universe = cs.build_universe(args.universe, token)
    if not universe:
        print("ERROR: empty universe", file=sys.stderr)
        sys.exit(1)
    print(f"[coil-ab] scanning {len(universe)} tickers @ "
          f"{datetime.now():%H:%M}...", file=sys.stderr)
    do_log(universe, token)


if __name__ == "__main__":
    main()
