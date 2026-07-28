# Broker MCP Directory — condensed snapshot

> **Source of truth:** [mphinance/awesome-broker-mcp](https://github.com/mphinance/awesome-broker-mcp).
> Every entry there was opened and read at the source (the broker's own docs or the
> server's own repo), carries a `last_verified` date, and says plainly what it can and
> can't do. This file is a **condensed mirror for fast in-agent lookup** — it will drift.
> **Always confirm the final pick against the live list**, which is re-verified regularly.
>
> Snapshot synced: 2026-07 · Directory verified upstream: 2026-07-16 · 65 entries upstream.

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | **Trades** — places a real order on its own tool call. |
| 📝 | **Draft only** — builds an order; *you* submit it in the broker's UI. Server can't. |
| 👁️ | **Read-only** — cannot place an order. Some are official and deliberate. |
| 🔀 | **Both** — ships two servers, one reads, one trades. |
| 💀 | **Dead upstream** — repo gone; only mirrors remain. |
| ❌ | **No MCP route** — checked, confirmed nothing exists. |

**Two independent axes people conflate:** *official vs. community* is **who wrote it**;
*local vs. remote* is **where it runs**. Alpaca and Kraken are official **and** local.

## Safety posture — the most useful sort order

| Posture | Who | What it means |
|---------|-----|---------------|
| Cannot execute, by design | Interactive Brokers | Server physically can't submit. No env var turns it on. |
| Draft-first, prompt-enforced | Trade It (aggregator) | Must draft, show you, and be told to execute. |
| Paper / sandbox by default | Alpaca · Kraken · Webull | Live is opt-in via env var or scope, server-side. |
| Live on a tool call | Robinhood · Tradier · most community | No broker-enforced approval; client config is the only guardrail. |
| Live, and no paper mode exists | Public.com | Confirm-first, but every confirmation is real money. |

## Official servers — equities & multi-asset

| Broker | Trades? | Notes | Type |
|--------|---------|-------|------|
| [Alpaca](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/alpaca.md) | ✅ | Equities, ETFs, crypto, multi-leg options, fixed income. 🛡️ Paper by default (`ALPACA_PAPER_TRADE=true`). | Local (`uvx`) |
| [Interactive Brokers](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/interactive-brokers.md) | 📝 | Global, multi-asset. 🛡️ Server *cannot* submit — you approve every order in IBKR's UI. | Remote |
| [Robinhood](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/robinhood.md) | ✅ | Stocks, options, futures. No server-side approval step. | Remote |
| [Tradier](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/tradier.md) | ✅ | Equities + multi-leg options. | Remote |
| [Webull](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/webull.md) | 🔀 | Cloud MCP read-only; `webull-openapi-mcp` (local) trades. 🛡️ Sandbox by default. | Remote + local |
| [TradeStation](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/tradestation.md) | ✅ | Needs paid AI tier + $10k balance. | Remote |
| [Public.com](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/public.md) | ✅ | ⚠️ **No paper mode — all orders live.** | Local |
| [eToro](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/etoro.md) | ⚠️ | Official MCP server is docs-only. Agent Portfolios trades but is REST, not MCP. | Remote |
| [Longbridge](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/longbridge.md) | ✅ | US + HK equities, options, warrants. ~148 tools. | Remote |
| [Tiger Brokers](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/tiger-brokers.md) | ✅ | US/HK/CN/SG. | Local (`uvx`) |
| [moomoo / Futu](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/moomoo.md) | ✅ | Full trading across HK/US/CN/SG/JP. Official route ships as Agent Skills; standalone `moomoo-api-mcp` is community. Needs OpenD gateway. | Local + OpenD |
| [Zerodha](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/zerodha-kite-connect.md) | ✅ | India equities, F&O, currency, commodities. Order placement on self-hosted build. | Remote + local |
| [Upstox](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/upstox.md) | 👁️ | India. Read-only by design. | Remote |

## Official servers — crypto (ahead of traditional brokers)

| Exchange | Trades? | Notes | Type |
|----------|---------|-------|------|
| [Kraken](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/kraken.md) | ✅ | Spot (1,400+ pairs), futures, tokenized stocks, forex. 🛡️ Paper built in; live opt-in per scope. | Local |
| [OKX](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/okx.md) | ✅ | Spot, swap, futures, options, grid bots. | Local |
| [Bybit](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/bybit.md) | ✅ | Spot, derivatives, positions. | Local |
| [Gemini](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/gemini.md) | ✅ | Full Gemini trading API. | Local |
| [Coinbase](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/coinbase.md) | ✅ | ⚠️ Onchain wallets/token swaps — not classic spot. | Local |
| [Crypto.com](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/crypto-com.md) | 👁️ | Market data only. | Remote |

## Official servers — forex / CFD

| Broker | Trades? | Notes | Type |
|--------|---------|-------|------|
| [cTrader (Spotware)](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/ctrader-spotware.md) | ✅ | FX, indices, commodities, crypto CFDs. | Remote + local |
| [ThinkMarkets](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/thinkmarkets.md) | ✅ | CFDs on ThinkTrader. | Remote |
| [TraderEvolution](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/traderevolution.md) | ✅ | 31 tools per vendor. | Unknown |
| [IG](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/ig.md) | 👁️ | Strictly read-only. | Remote |

## Community servers (third-party — not broker-endorsed; check the last commit)

| Broker | Trades? | Notes | Type |
|--------|---------|-------|------|
| [tastytrade](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/tastytrade.md) | ✅ | Equities, options, futures, multi-leg. | Local or Modal |
| [Charles Schwab](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/schwab.md) | ✅ | Equities, options, brackets/OCO. Opt-in required. | Local |
| [eToro](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/etoro.md) | ✅ | 35 tools; the only eToro route that is both MCP *and* trading-capable. | Local (`npx`) |
| [Saxo Bank](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/saxo-bank.md) | ✅ | Equities, FX, CFDs, futures, options. 🛡️ Writes triple-gated, SIM by default. | Local |
| [Angel One](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/angel-one.md) | ✅ | India equities + F&O via SmartAPI. | Local |
| [NinjaTrader](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/ninjatrader.md) | ✅ | Futures, via connected NT8 desktop install. | Local |
| [Tradovate](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/tradovate.md) | ✅ | Futures — market/limit, configurable TIF. | Local |
| [Kalshi](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/kalshi.md) | ✅ | Event contracts. | Local |
| [Polymarket](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/polymarket.md) | ✅ | Outcome tokens — market + limit. | Local |
| [Binance](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/binance.md) | ✅ | ⚠️ Varies by repo — no single canonical server. | Local |
| [Hyperliquid](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/hyperliquid.md) | ✅ | Perpetuals and spot on the DEX. | Local |
| [Fidelity](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/fidelity.md) | ✅ | ⚠️ Drives Fidelity's site with Playwright — your password + 2FA. `dry_run` defaults true. | Local |
| [Trading 212](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/trading212.md) | ✅ | Official beta API. ⚠️ Quickstart config hardcodes `live`. | Local |
| [XTB](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/xtb.md) | 💀 | Upstream repo deleted; survives only as mirrors. | Local |
| [E*TRADE](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/etrade.md) | 👁️ | Client lib has `place_order`; MCP surface never registers it. Cannot trade. | Local |
| [OANDA](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/oanda.md) | 👁️ | Read-only. The one "order-capable" server isn't MCP at all. | Local |
| [Questrade](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/questrade.md) | 👁️ | Read-only. | Local |
| [Trade Republic](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/trade-republic.md) | 👁️ | ⚠️ Reverse-engineers a private API; may violate ToS. | Local |
| [Deriv](https://github.com/mphinance/awesome-broker-mcp/blob/main/brokers/deriv.md) | 👁️ | Read-only, 2 tools. | Local |

## Aggregators (one endpoint, many brokers — almost all read-only)

| Aggregator | Trades? | Covers |
|------------|---------|--------|
| [Trade It](https://github.com/mphinance/awesome-broker-mcp/blob/main/aggregators/trade-agent.md) | ✅ 🛡️ draft-first, explicit confirm | Robinhood, Schwab, E*TRADE, Webull, Public, tastytrade, Coinbase, Kraken |
| [ConnectTrade](https://github.com/mphinance/awesome-broker-mcp/blob/main/aggregators/connecttrade.md) | ✅ early access, guardrails undocumented | 20+ incl. Alpaca, Lightspeed, TradeZero, Webull, TradeStation |
| [SnapTrade](https://github.com/mphinance/awesome-broker-mcp/blob/main/aggregators/snaptrade.md) | 👁️ read-only | Robinhood, Schwab, Fidelity, Vanguard, E*TRADE, Alpaca, Tradier, Trading 212 |
| [Truthifi](https://github.com/mphinance/awesome-broker-mcp/blob/main/aggregators/truthifi.md) | 👁️ read-only | 18,000+ institutions |
| [Plaid](https://github.com/mphinance/awesome-broker-mcp/blob/main/aggregators/plaid.md) | 👁️ read-only | Official account data |
| [Teller](https://github.com/mphinance/awesome-broker-mcp/blob/main/aggregators/teller.md) | 👁️ read-only | Community |

## Confirmed NO MCP route (checked, confirmed negative)

SoFi · JP Morgan/Chase · Merrill · Ally Invest · M1 Finance · Wealthfront · Betterment ·
Stash · DEGIRO · Hargreaves Lansdown · TradeZero · Lightspeed · AMP Futures/Rithmic ·
FOREX.com (StoneX) · MX · Vanguard (reachable read-only via SnapTrade/Truthifi only).

If a user's broker is here, that's a real answer — it saves them the afternoon. See the
[live list](https://github.com/mphinance/awesome-broker-mcp) for notes on each.
