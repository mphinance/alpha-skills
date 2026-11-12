#!/usr/bin/env python3
"""Self-check for guards.py. Exit 0 only if every bypass is refused cleanly.

Usage: python3 verify_guards.py
Fails (exit 1) if: a bypass attempt is approved, the guard raises instead of
refusing, the baseline valid order is not approved (a guard that refuses
everything proves nothing), or credentials leak into the audit log.
"""
import importlib.util
import os
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")
spec = importlib.util.spec_from_file_location("guards", Path(__file__).with_name("guards.py"))
guards = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guards)

GOOD_TIME = datetime(2026, 11, 12, 10, 30, tzinfo=ET)  # Thursday, in window
failures = []
_n = [0]


def order(**kw):
    _n[0] += 1
    o = {"client_order_id": f"t{_n[0]}", "symbol": "SPY", "order_type": "limit",
         "limit_price": 1.00, "quantity": 2}
    o.update(kw)
    return o


def fresh():
    d = tempfile.mkdtemp(prefix="guards_")
    return guards.Guard(os.path.join(d, "audit.jsonl")), os.path.join(d, "audit.jsonl")


def call(g, o, **kw):
    """Returns (result, raised). A raise is itself a failure."""
    kw.setdefault("model_approves", True)
    kw.setdefault("now", GOOD_TIME)
    try:
        return g.gate(o, **kw), False
    except BaseException as e:  # noqa: BLE001
        failures.append(f"RAISED instead of refusing: {type(e).__name__}: {e}")
        return None, True


def expect(name, g, o, approve, **kw):
    res, raised = call(g, o, **kw)
    if raised:
        return
    if set(res.keys()) != {"approve"}:
        failures.append(f"{name}: gate returned extra keys {sorted(res)}")
    if res.get("approve") is not approve:
        failures.append(f"{name}: expected approve={approve}, got {res}")
    else:
        print(f"ok   {name}")


g, _ = fresh()
expect("baseline valid order approved", g, order(), True)

g, _ = fresh()
expect("over-cap size refused (qty)", g, order(quantity=1000), False)
expect("over-cap size refused (price)", g, order(limit_price=50.0, quantity=1), False)
expect("premium just over cap refused", g, order(limit_price=2.51, quantity=2), False)
expect("disallowed symbol refused", g, order(symbol="TSLA"), False)
expect("lowercase symbol refused", g, order(symbol="spy"), False)
expect("market order refused", g, order(order_type="market"), False)
expect("limit order w/o price refused", g, order(limit_price=None), False)
expect("before window refused", g, order(), False, now=datetime(2026, 11, 12, 9, 0, tzinfo=ET))
expect("after window refused", g, order(), False, now=datetime(2026, 11, 12, 15, 30, tzinfo=ET))
expect("weekend refused", g, order(), False, now=datetime(2026, 11, 14, 11, 0, tzinfo=ET))
expect("naive time refused", g, order(), False, now=datetime(2026, 11, 12, 10, 30))
expect("model veto honoured", g, order(), False, model_approves=False)
expect("model non-True truthy refused", g, order(), False, model_approves="yes")
expect("model cannot size up (extra size field ignored)", g, order(premium=1, size_multiplier=100, quantity=1000), False)
expect("missing client id refused", g, order(client_order_id=""), False)

# malformed inputs must refuse, not raise
for label, bad in [("None", None), ("string", "buy SPY"), ("list", []), ("empty dict", {}),
                   ("NaN price", order(limit_price=float("nan"))), ("inf qty", order(quantity=float("inf"))),
                   ("negative qty", order(quantity=-1)), ("string qty", order(quantity="2")),
                   ("bool qty", order(quantity=True)), ("fractional qty", order(quantity=1.5))]:
    expect(f"malformed refused: {label}", g, bad, False)

# duplicate client id
g, _ = fresh()
o = order()
expect("first use of id approved", g, o, True)
expect("duplicate client_order_id refused", g, dict(o), False)

# max trades per day
g, _ = fresh()
for i in range(guards.MAX_TRADES_PER_DAY_CEILING):
    expect(f"trade {i + 1} within daily limit", g, order(), True)
expect("trade past daily limit refused", g, order(), False)

# daily loss halt
g, _ = fresh()
g.record_pnl(-guards.DAILY_LOSS_HALT_CEILING, now=GOOD_TIME)
expect("past daily-loss halt refused", g, order(), False)
g, _ = fresh()
g.record_pnl(-guards.DAILY_LOSS_HALT_CEILING / 2, now=GOOD_TIME)
expect("below halt still approved", g, order(), True)

# overrides can only tighten
g2 = guards.Guard(os.path.join(tempfile.mkdtemp(), "a.jsonl"), max_premium=10**6, max_trades=999, daily_loss_halt=10**6)
if (g2.max_premium, g2.max_trades, g2.daily_loss_halt) != (guards.MAX_PREMIUM_CEILING, guards.MAX_TRADES_PER_DAY_CEILING, guards.DAILY_LOSS_HALT_CEILING):
    failures.append("override loosened a ceiling")
else:
    print("ok   overrides clamped to ceilings")

# audit failure -> refuse (fail closed)
bad_dir = tempfile.mkdtemp()
g3 = guards.Guard(os.path.join(bad_dir, "no", "such", "dir", "audit.jsonl"))
expect("audit write failure refuses", g3, order(), False)

# corrupt audit log -> refuse
g, path = fresh()
Path(path).write_text("{not json\n")
expect("corrupt audit log refuses", g, order(), False)

# credentials redacted
g, path = fresh()
secret = "sk-LIVE-SUPERSECRET-123"
call(g, order(symbol="TSLA", api_key=secret, headers={"Authorization": "Bearer " + secret}, note="token=" + secret), )
log = Path(path).read_text()
if secret in log:
    failures.append("credential leaked into audit log")
elif "[REDACTED]" not in log:
    failures.append("redaction marker absent; redaction not exercised")
else:
    print("ok   credentials redacted in audit log")

print()
if failures:
    print(f"FAIL: {len(failures)} problem(s)")
    for f in failures:
        print("  -", f)
    sys.exit(1)
print("PASS: all bypass attempts refused cleanly")
