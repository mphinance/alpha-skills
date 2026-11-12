#!/usr/bin/env python3
"""Hard guards for the Ghost Auto-Trader order path. Standard library only.

The gate returns ONLY {"approve": bool}. Reasons go to the JSONL audit log.
Sizing, strike and price are computed by your code, never by the model. The
model's only input is `model_approves`: it can veto, it can never size up.

Fails closed: any exception, malformed input, or audit-write failure -> refuse.
Limits are module constants; Guard(overrides) can only TIGHTEN them (values are
clamped to the ceilings below).

Not a human gate. See SKILL.md "What is code-enforced".
"""
import json
import math
import os
import re
import threading
from datetime import datetime, time as dtime
from zoneinfo import ZoneInfo

ET = ZoneInfo("America/New_York")

# ---- hard ceilings (edit here, in code review, not at runtime) -------------
MAX_PREMIUM_CEILING = 500.0        # USD premium per trade (price * qty * 100)
MAX_TRADES_PER_DAY_CEILING = 3
DAILY_LOSS_HALT_CEILING = 300.0    # halt when realized loss today >= this (USD)
ALLOWED_SYMBOLS = frozenset({"SPY", "QQQ"})
ALLOWED_ORDER_TYPES = frozenset({"limit"})
WINDOW_START = dtime(9, 45)        # ET, inclusive
WINDOW_END = dtime(15, 0)          # ET, exclusive
CONTRACT_MULTIPLIER = 100

_SECRET_KEY = re.compile(
    r"(api[_-]?key|secret|token|password|passwd|authorization|bearer|private[_-]?key|access[_-]?key)",
    re.I)
_SECRET_VAL = re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._\-]+|((?:api[_-]?key|token|secret|password)\s*[=:]\s*)[^\s,;&\"']+")
_lock = threading.Lock()


def redact(obj):
    """Return a copy of obj with credential-looking values replaced."""
    if isinstance(obj, dict):
        return {k: ("[REDACTED]" if _SECRET_KEY.search(str(k)) else redact(v)) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [redact(v) for v in obj]
    if isinstance(obj, str):
        return _SECRET_VAL.sub(lambda m: (m.group(1) or m.group(2)) + "[REDACTED]", obj)
    return obj


def _num(x):
    """Finite positive real number or raise. Rejects bool, NaN, inf, strings."""
    if isinstance(x, bool) or not isinstance(x, (int, float)):
        raise ValueError("not a number")
    if not math.isfinite(x) or x <= 0:
        raise ValueError("not finite positive")
    return float(x)


class Guard:
    def __init__(self, audit_path, max_premium=None, max_trades=None, daily_loss_halt=None):
        self.audit_path = audit_path
        self.max_premium = min(MAX_PREMIUM_CEILING, _num(max_premium)) if max_premium is not None else MAX_PREMIUM_CEILING
        self.max_trades = min(MAX_TRADES_PER_DAY_CEILING, int(_num(max_trades))) if max_trades is not None else MAX_TRADES_PER_DAY_CEILING
        self.daily_loss_halt = min(DAILY_LOSS_HALT_CEILING, _num(daily_loss_halt)) if daily_loss_halt is not None else DAILY_LOSS_HALT_CEILING

    # ---- audit log ---------------------------------------------------------
    def _append(self, entry):
        line = json.dumps(redact(entry), sort_keys=True, default=str)
        with _lock:
            with open(self.audit_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")
                f.flush()
                os.fsync(f.fileno())

    def _read(self):
        if not os.path.exists(self.audit_path):
            return []
        out = []
        with open(self.audit_path, encoding="utf-8") as f:
            for ln in f:
                ln = ln.strip()
                if ln:
                    out.append(json.loads(ln))  # corrupt log raises -> caller refuses
        return out

    def record_pnl(self, realized_pnl, now=None):
        """Code (not the model) reports realized P&L of a closed trade."""
        now = (now or datetime.now(ET)).astimezone(ET)
        self._append({"event": "pnl", "day": now.date().isoformat(), "pnl": float(realized_pnl)})

    # ---- the gate ----------------------------------------------------------
    def gate(self, order, model_approves=False, now=None):
        """Return {"approve": bool}. Never raises."""
        try:
            return {"approve": bool(self._decide(order, model_approves, now))}
        except BaseException as exc:  # noqa: BLE001 - fail closed on anything
            if isinstance(exc, (KeyboardInterrupt, SystemExit)):
                raise
            try:
                self._append({"event": "decision", "approve": False, "reason": "guard_error:" + type(exc).__name__})
            except Exception:
                pass
            return {"approve": False}

    def _decide(self, order, model_approves, now):
        now = (now or datetime.now(ET))
        if now.tzinfo is None:
            return self._refuse(order, "naive_time", now)
        now = now.astimezone(ET)
        if not isinstance(order, dict):
            return self._refuse(None, "order_not_dict", now)
        if model_approves is not True:                      # model may only veto
            return self._refuse(order, "model_veto", now)
        cid = order.get("client_order_id")
        if not isinstance(cid, str) or not cid.strip():
            return self._refuse(order, "no_client_order_id", now)
        if order.get("symbol") not in ALLOWED_SYMBOLS:
            return self._refuse(order, "symbol_not_allowed", now)
        if order.get("order_type") not in ALLOWED_ORDER_TYPES:
            return self._refuse(order, "order_type_not_allowed", now)
        try:
            price = _num(order.get("limit_price"))
            qty = _num(order.get("quantity"))
        except ValueError:
            return self._refuse(order, "bad_price_or_qty", now)
        if qty != int(qty):
            return self._refuse(order, "fractional_qty", now)
        premium = price * qty * CONTRACT_MULTIPLIER          # computed here, never trusted from caller
        if premium > self.max_premium:
            return self._refuse(order, "premium_over_cap", now)
        if now.weekday() >= 5 or not (WINDOW_START <= now.time() < WINDOW_END):
            return self._refuse(order, "outside_window", now)

        entries = self._read()
        day = now.date().isoformat()
        if any(e.get("event") == "decision" and e.get("approve") and e.get("client_order_id") == cid for e in entries):
            return self._refuse(order, "duplicate_client_order_id", now)
        todays = [e for e in entries if e.get("day") == day]
        pnl = sum(e.get("pnl", 0.0) for e in todays if e.get("event") == "pnl")
        if pnl <= -self.daily_loss_halt:
            return self._refuse(order, "daily_loss_halt", now)
        n = sum(1 for e in todays if e.get("event") == "decision" and e.get("approve"))
        if n >= self.max_trades:
            return self._refuse(order, "max_trades_per_day", now)

        # audit BEFORE approving; if this raises, gate() refuses
        self._append({"event": "decision", "approve": True, "reason": "ok", "day": day,
                      "client_order_id": cid, "symbol": order["symbol"], "premium": premium,
                      "ts": now.isoformat()})
        return True

    def _refuse(self, order, reason, now):
        entry = {"event": "decision", "approve": False, "reason": reason, "day": now.date().isoformat(), "ts": now.isoformat()}
        if isinstance(order, dict):
            entry["order"] = order
        self._append(entry)
        return False
