---
name: broker-mcp-selector
description: Pick a broker MCP server your AI agent can actually execute trades through, and wire it up safely. Use when the user wants to place, submit, or automate real orders; connect an agent to a brokerage account; choose between Alpaca, IBKR, Tradier, Robinhood, Schwab, Kraken and other broker MCP servers; move from analysis to execution; or check whether a broker's MCP server can trade, is read-only, or is safe to connect to real money. This is the "hands" that execute what the rest of the Alpha Skills suite decides.
---

# Broker MCP Selector

## Overview

The rest of the Alpha Skills suite is the **brain** — it screens, scores, detects
regimes, and produces a trade plan. This skill is the **hands**: it answers the next
question, *"where do I actually place this order, and is it safe to let an agent do it?"*

It selects a broker [MCP](https://modelcontextprotocol.io) server for execution based on
what the user trades, where they are, and how much autonomy they're comfortable giving an
agent — then walks them through connecting it with safe defaults.

The authoritative, continuously re-verified data behind this skill lives in
**[awesome-broker-mcp](https://github.com/mphinance/awesome-broker-mcp)** — a directory
where every entry was opened and read at the source (the broker's own docs or the server's
own repo). A condensed snapshot ships in `references/brokers.md`; **always prefer the live
list** for the final decision, because this space moves fast and a stale entry is how
someone wires an agent to the wrong thing.

## When to Use

Invoke this skill when the user wants to:
- "Actually place the trade" / "submit this order" / "execute this"
- "Connect my agent to my brokerage" / "wire up execution"
- "Which broker can Claude trade through?" / "does <broker> have an MCP server?"
- "Set up an auto-trader" / "automate my strategy" (pair with `ghost-auto-trader`)
- "Is it safe to let an AI place orders on my account?"
- Move from a plan produced by any screener/analysis skill to a live or paper order
- Choose between broker MCP servers, or check if one is read-only vs. trade-capable

## The two questions that decide almost everything

Before recommending anything, establish these — they collapse the whole option space:

1. **Who wrote the server, and can it actually place an order?**
   - `✅ Trades` — places a real order on its own tool call.
   - `📝 Draft only` — builds the order; the *human* submits it in the broker's UI. The
     server physically cannot submit (e.g. Interactive Brokers).
   - `👁️ Read-only` — cannot place an order. Often official and deliberate. Most people
     wiring up an LLM for *analysis* want exactly this.
   - **"Has an MCP server" ≠ "can trade."** Some official servers are docs-only or
     read-only; some community repos claim MCP but never register a trading tool. Verify
     the tool surface, not the marketing.

2. **What's the safety posture if the agent does something careless?**
   From safest to sharpest (see `references/brokers.md` for who sits where):
   - **Cannot execute, by design** (IBKR draft-approval) — no env var turns it on.
   - **Draft-first, prompt-enforced** (Trade It) — must draft, show, be told to execute.
   - **Paper / sandbox by default** (Alpaca, Kraken, Webull) — live is opt-in, server-side.
   - **Live on a tool call** (Robinhood, Tradier, most community servers) — the only
     guardrail is your client config.
   - **Live, and no paper mode exists** (Public.com) — every confirmation is real money.

## Workflow

### Step 1: Scope the need
Ask (or infer from prior suite output):
- **Asset class** — equities, options, futures, crypto, FX/CFD, event contracts.
- **Region** — US, India, Asia, EU, crypto (global).
- **Autonomy** — analysis only, human-in-the-loop draft approval, or full auto-execution.
- **Environment** — remote/hosted (paste a URL) vs. local (a process on their machine).

If the honest answer is *"I just want analysis,"* recommend **read-only** and stop. Least
privilege: analysis needs no trading scope, and it removes the entire "prompt injection
reaches my account" blast radius.

### Step 2: Match against the directory
Read `references/brokers.md`, then **confirm against the live list**
(https://github.com/mphinance/awesome-broker-mcp) before finalizing. Narrow by asset
class + region, then rank by the safety posture the user asked for.

Sensible defaults when the user is unsure:
- **Safest thing that still trades** → [Interactive Brokers](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/interactive-brokers.md) (draft-approval, server cannot submit).
- **Experiment without risking money** → [Alpaca](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/alpaca.md) or [Kraken](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/kraken.md) (paper/sandbox by default).
- **Analysis only** → [SnapTrade](https://github.com/mphinance/awesome-broker-mcp/blob/main/aggregators/snaptrade.md) / [Truthifi](https://github.com/mphinance/awesome-broker-mcp/blob/main/aggregators/truthifi.md) (read-only by design).
- **Crypto** → Kraken, OKX, Bybit, Gemini (all official, all trade).
- **India** → Zerodha (trades, self-hosted) or Upstox (read-only).

### Step 3: Present the recommendation
Give the user a short, decision-shaped answer:

```markdown
## Recommended: <Broker> MCP

- **Can it trade?** <✅ / 📝 / 👁️> — <one line>
- **Safety posture:** <posture> — <what happens on a careless prompt>
- **Type:** <Local (uvx/npx) / Remote / needs a gateway>
- **Official or community?** <who wrote it — and if community, "strangers' code holding
  your credentials; check the last commit">
- **Why this one:** <ties back to their asset class / region / autonomy answer>
- **Source:** <link to the awesome-broker-mcp page for this broker>

### Safer alternative
<If the pick is "live on a tool call," always name the draft-first or paper-default
option they could use instead.>
```

### Step 4: Wire it up with safe defaults
- Turn paper/sandbox **on** and leave live **off** until the user has watched it behave.
  Name the exact switch (e.g. Alpaca `ALPACA_PAPER_TRADE=true`; Kraken paper scope on,
  trade scope off).
- Where the server supports it, **leave the trading tools out entirely** server-side
  (e.g. Alpaca `ALPACA_TOOLSETS`) if the user only needs data.
- Prefer draft-first execution when available. For full automation, hand off to
  [`ghost-auto-trader`](../ghost-auto-trader/) and keep an explicit approval gate.
- For portfolio *reads* feeding analysis, hand off to
  [`portfolio-manager`](../portfolio-manager/).

### Step 5: State the risks plainly
Before any live connection, surface these (don't bury them):
- **Prompt injection reaches your account.** If the agent reads a webpage, email, or
  Discord message, hostile text is one hop from an order once it also holds a trading tool.
- **Separate the brain from the hands.** Analysis and execution don't have to be — and
  arguably shouldn't be — the same connector.
- **Paper first, for longer than feels necessary.** Nothing here is battle-tested at the
  level your money assumes.

## Reference Files

**references/brokers.md**
- When: matching a need to a broker, or checking trade-capability / safety posture.
- Contains: a condensed, attributed snapshot of the awesome-broker-mcp directory —
  official/community/aggregator servers, what each trades, local vs. remote, and safety
  posture. Always cross-check the live list before finalizing.

## Relationship to the rest of the suite

| Stage | Skill | Role |
|-------|-------|------|
| Decide *what* to trade | screeners, regime detectors, `stanley-druckenmiller-investment` | the brain |
| Decide *where* to execute | **broker-mcp-selector** (this skill) | the hands |
| Read the account | `portfolio-manager` | eyes on positions |
| Automate execution | `ghost-auto-trader` | the trigger finger (with a gate) |

## Limitations and Disclaimers

*This skill helps you choose and connect tooling. It is not financial advice and not an
endorsement of any broker or server. Community servers are third-party code that will hold
your broker credentials — read them, check the last commit, and assume the maintainer may
walk away. Verify every capability against the source before connecting to real money.*
