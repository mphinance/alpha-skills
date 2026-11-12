---
name: ghost-auto-trader
description: "Architect and deploy the Ghost Auto-Trader framework: a zero-DTE options trading pipeline using TradingView webhooks, AI-gate validation, and broker execution."
---

# Ghost Auto-Trader Architecture

This skill helps you deploy the Ghost Alpha Trading System for 0DTE options.

## Architecture Pipeline
1. **Signal Generation:** TradingView fires a "Ghost Alpha Grade A" alert based on momentum squeeze metrics.
2. **Webhook Receiver:** A Python FastAPI/Flask backend receives the signal payload containing ticker, timeframe, grade, and relative volume.
3. **The AI Gate:** The payload is sent to an LLM (e.g., Gemini Flash) for immediate contextual validation (checking macro alignment and news sentiment).
4. **Execution:** If the AI gate approves, the system automatically buys the ATM/OTM 0DTE option via the broker API (e.g., Tradier).
5. **Position Management:** A rigid 30-second monitor loop enforces +50% Take Profit, -40% Stop Loss, and a hard 3:00 PM ET time-based exit.

## Choosing the execution broker

This pipeline places **live orders on a tool call** — the AI gate is the only thing
between a signal and a filled position, so the broker you wire in matters as much as the
strategy. Before hardcoding a broker API:

- Use the [`broker-mcp-selector`](../broker-mcp-selector/) skill to choose one, or check
  the broker directly in
  **[awesome-broker-mcp](https://github.com/mphinance/awesome-broker-mcp)**.
- The default here, [Tradier](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/tradier.md),
  is *live on a tool call* — there is no broker-enforced approval step, so your risk
  parameters and the AI gate are the entire guardrail. Size and test accordingly.
- **Paper/sandbox first.** Run the full pipeline against a paper account for far longer
  than feels necessary before pointing it at real money. Prompt injection into the
  signal or news feed reaches the order in this design.

## Usage
When the user asks to "set up a trading bot" or "build an auto-trader":
1. Scaffold the `main.py` webhook listener.
2. Scaffold the `auto_trader.py` execution engine with the AI gate.
3. Copy `scripts/guards.py` into the project and call `Guard.gate()` immediately before every broker call. Run `python3 scripts/verify_guards.py` in CI; it must exit 0.

## Guard code (`scripts/guards.py`, `scripts/verify_guards.py`)

`Guard.gate(order, model_approves, now)` returns only `{"approve": bool}`; reasons go to a JSONL audit log with credentials redacted. Premium is computed in code from price, quantity and the contract multiplier. The model supplies one input, `model_approves`, so it can veto but never size up (extra size fields are ignored). Any exception, malformed input, corrupt log or failed audit write refuses.

**Code-enforced (checked by `verify_guards.py`):**
- max premium per trade, max trades per day, daily-loss halt (ceilings are module constants; overrides can only tighten)
- SPY/QQQ allowlist, limit orders only, weekday 09:45-15:00 ET window
- duplicate `client_order_id` refused; audit entry written before approval
- credential redaction in the audit log
- refuses cleanly rather than raising

**Still prose / not enforced by this code:**
- the TradingView signal, the LLM prompt and the strike/expiry selection logic (yours to write, in code)
- the +50% / -40% / 3:00 PM exit loop is not part of the guard
- paper vs live: see [`order-lifecycle-safety`](../order-lifecycle-safety/) for the environment-proof preflight; the guard does not check it
- reconcile-before-retry after an unknown outcome; the guard only blocks duplicate ids it has seen approved
- the daily-loss halt only sees P&L your code reports through `record_pnl()`

**This is not a human gate.** An agent with filesystem access can edit `guards.py`, its ceilings, or the audit log, or call the broker directly bypassing the gate. It becomes a human gate only if arming happens in a terminal the agent cannot reach (separate user or machine, credentials the agent process never holds). Without that, treat the guard as a safety net against mistakes and prompt injection, not against a compromised agent.
