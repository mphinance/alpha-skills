---
name: webull-openapi
description: Trade stocks, options, futures, crypto, and event contracts on Webull. Query real-time and historical market data. Manage accounts and positions. Supports US, HK, JP, SG, TH, MY, UK, MX, BR, EU, ZA, and AU regions with configurable risk controls.
---

# Webull OpenAPI Skill

This skill lets you interact with Webull's trading platform through natural language. You can place orders, check market data, query account info, and manage positions — all via the official Webull Python SDK.

## What You Can Do

- **Trade**: Place, preview, modify, and cancel orders for stocks, options, futures, crypto, and event contracts. Each asset type has dedicated actions:
  - Stock/ETF → `place`, `preview`, `replace`
  - Option → `option-place`, `option-preview`, `option-replace`, `option-strategy-place`
  - Futures → `futures-place`, `futures-replace`
  - Crypto → `crypto-place`
  - Event → `event-place`, `event-replace`
- **Market Data**: Get real-time snapshots, historical bars, tick data, quotes, and order flow for all asset classes (stocks, options, futures, crypto, event contracts)
  - Option market data actions: `option-snapshot`, `option-bars`, `option-tick` (category: US_OPTION, supports US/HK/JP)
- **Accounts**: List accounts, check balances, view positions
- **Instruments**: Look up stock, crypto, futures, option, and event contract instruments; get company profile, analyst ratings, and target prices
  - Option contracts: `instrument-option-contracts` (query by underlying symbol, expiry, strike, etc.)
- **Screener**: Top gainers/losers, most active stocks, market sectors, high dividend, and 52-week high/low
- **Fundamentals**: Financial statements, capital flow, industry comparison, earnings/dividend calendar, forecast EPS, and fund/ETF data
- **Watchlist**: Create, manage, and query watchlists and their instruments

## Safety Rules

**All order-mutating operations require user confirmation before execution.**

Mutating actions: `place`, `replace`, `cancel`, `batch-place`, `algo-place`, `option-place`, `option-replace`, `option-strategy-place`, `futures-place`, `futures-replace`, `crypto-place`, `event-place`, `event-replace`.

Before executing any of these operations, the AI must:
1. Display a clear summary of the operation to the user, including:
   - Action type (place / replace / cancel)
   - Symbol, side, order type, quantity, price
   - Account being used
2. Explicitly ask the user to confirm (e.g., "Confirm this order? [Yes/No]")
3. Only proceed after receiving explicit user approval

Read-only operations (`account-list`, `balance`, `position`, `open`, `history`, `detail`, `instrument-*`, all `market-data` actions) do not require confirmation and can be executed immediately.

---

## Quick Examples

> **CLI command:** After `pip install -e .`, use `webull-skill` on all platforms (macOS, Linux, Windows). This console entry point is bound to the Python that ran `pip`, so it works regardless of what `python3` or `python` points to on your system.

> **Passing order JSON:** Prefer `--order-file <path>` (write JSON to a temp file first) over `--order-json '<inline>'`. Inline JSON with `--order-json` is fragile across shells — Windows bash, PowerShell, and some macOS terminals mangle quotes and escapes. Using `--order-file` avoids all shell quoting issues.

```bash
# Check your accounts
webull-skill trading --action account-list

# Get AAPL stock price
webull-skill market-data --action stock-snapshot --symbols AAPL

# Get account balance
webull-skill trading --action balance --account-id <id>

# Place a limit buy order (recommended: use --order-file)
#   echo '{"symbol":"AAPL","side":"BUY","order_type":"LIMIT","limit_price":180,"quantity":10,"instrument_type":"EQUITY","market":"US","time_in_force":"DAY","entrust_type":"QTY","support_trading_session":"CORE","combo_type":"NORMAL"}' > /tmp/order.json
#   webull-skill trading --action place --account-id <id> --order-file /tmp/order.json

# Cancel an order
webull-skill trading --action cancel --account-id <id> --client-order-id <oid>
```

## CLI Entry Point

```
webull-skill [--env-file PATH] [--verbose-sdk-log] <module> --action <ACTION> [options]
```

Three modules: `trading`, `market-data`, `auth`.

---

## Modules

### trading

Instrument queries, account/asset operations, and all order operations (stock, option, futures, crypto, event contracts).

For full action list, order JSON formats, replace rules, and order type references, see [Trading Guide](references/skill_trading.md).

### market-data

Real-time and historical market data for all asset classes (stock, option, futures, crypto, event contracts), plus screener, fundamentals, and watchlist.

For full action list, options, category values, and examples, see [Market Data Guide](references/skill_market_data.md).

### auth

```bash
webull-skill auth
```

Interactive 2FA authentication. Run once before first use. The SDK waits up to 5 minutes for you to approve in the Webull mobile app. Token is cached and auto-refreshes.

---

## Output Format

All operations output formatted text directly to stdout, with a region-aware disclaimer at the top:

```
⚠️ Disclaimer: The information provided by this tool is for reference only ...

=== Stock Snapshot: AAPL ===
  Symbol:          AAPL
  Price:           255.92
  Pre Close:       255.63
  Change:          0.29
  ...
```

- Success: disclaimer + formatted data to stdout, exit code 0
- Error: error message to stderr, exit code 1
- US/JP/SG/TH/MY/UK/MX/BR/EU/ZA/AU region: English disclaimer only
- HK region: English + Simplified Chinese + Traditional Chinese disclaimer

---

## Configuration

Via `.env` file or environment variables. Required:

```
WEBULL_APP_KEY=<your_app_key>
WEBULL_APP_SECRET=<your_app_secret>
```

Region selection:

```env
# Choose one region:
WEBULL_REGION_ID=us
# WEBULL_REGION_ID=hk
# WEBULL_REGION_ID=jp
# WEBULL_REGION_ID=sg
# WEBULL_REGION_ID=th
# WEBULL_REGION_ID=my
# WEBULL_REGION_ID=uk
# WEBULL_REGION_ID=mx
# WEBULL_REGION_ID=br
# WEBULL_REGION_ID=eu
# WEBULL_REGION_ID=za
# WEBULL_REGION_ID=au

# Sandbox by default; set prod only for live trading.
WEBULL_ENVIRONMENT=uat
```

**`.env` lookup order** (when `--env-file` is not specified):
1. `$WEBULL_CONFIG_DIR/.env` — if `WEBULL_CONFIG_DIR` is set
2. `<project_root>/.env` — default (sibling of `webull_skill/`)
3. Current working directory `.env` — last resort

> To keep credentials outside the project directory, set `WEBULL_CONFIG_DIR` as a **system environment variable** (e.g. in `~/.zshrc`), then place your `.env` at `$WEBULL_CONFIG_DIR/.env`. Setting `WEBULL_CONFIG_DIR` inside a `.env` file has no effect — it must be set before the process starts.

Optional:

| Variable | Default | Description |
|----------|---------|-------------|
| `WEBULL_ENVIRONMENT` | `uat` | `uat` (sandbox) or `prod` (live) |
| `WEBULL_REGION_ID` | `us` | `us`, `hk`, `jp`, `sg`, `th`, `my`, `uk`, `mx`, `br`, `eu`, `za`, or `au` |
| `WEBULL_MAX_ORDER_NOTIONAL_USD` | `10000` | Max order value (USD) |
| `WEBULL_MAX_ORDER_NOTIONAL_HKD` | `80000` | Max order value for HK market (HKD) |
| `WEBULL_MAX_ORDER_NOTIONAL_CNH` | `70000` | Max order value for CN market (CNH) |
| `WEBULL_MAX_ORDER_NOTIONAL_JPY` | `1500000` | Max order value for JP market (JPY) |
| `WEBULL_MAX_ORDER_QUANTITY` | `1000` | Max shares per order |
| `WEBULL_SYMBOL_WHITELIST` | (none) | Comma-separated allowed symbols |
| `WEBULL_CONFIG_DIR` | (none) | **System env var only** (not in `.env`). Moves `.env` lookup and token storage to this directory |
| `WEBULL_TOKEN_DIR` | `<project_root>/conf/` | Token storage directory |
| `WEBULL_AUDIT_LOG_FILE` | (stderr) | Audit log file path |
| `WEBULL_LOG_LEVEL` | `WARNING` | SDK log level |

---

## Region Support

| Feature | US | HK | JP | SG | TH | MY | UK | MX | BR | EU | ZA | AU |
|---------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Stock trading | ✓ | ✓ (US/HK/CN) | ✓ (US/JP) | ✓ (US) | ✓ (US) | ✓ (US) | ✓ (US) | ✓ (US) | ✓ (US) | ✓ (US) | ✓ (US) | ✓ (US) |
| Options | ✓ | ✓ (US only) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Futures | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Crypto | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Event contracts | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Combo orders | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Algo orders | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Trailing stop loss | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Fractional shares | ✓ (US market) | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Company profile | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Analyst rating / target price | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| NOII bars / snapshot | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Screener | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Watchlist | ✓ | ✓ | ✓ | ✗ | ✓ | ✓ | ✓ | ✗ | ✗ | ✗ | ✗ | ✗ |
| Fundamentals | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |


### HK-Specific Notes

- HK stocks use order types: `ENHANCED_LIMIT`, `AT_AUCTION`, `AT_AUCTION_LIMIT`
- CN A-shares (Stock Connect): `LIMIT` only, disabled by default — contact Webull to enable
- Board lot sizes vary by HK stock
- No combo orders, algo orders, crypto, or event contracts in HK region
- HK stock orders (institutional/broker): require `sender_sub_id` and `no_party_ids` (BCAN)
- HK US options (institutional/broker): support `sender_sub_id` only, no BCAN needed

### JP-Specific Notes

- Configure JP with `WEBULL_REGION_ID=jp`; sandbox uses `WEBULL_ENVIRONMENT=uat`.
- JP supports stock/ETF market data and stock order management. Futures, crypto, event contracts, options, combo orders, and algo orders are not supported in JP.
- JP stock instrument categories are `US_STOCK` and `US_ETF`.
- JP stock order markets are `US` and `JP`.
- JP market orders support `LIMIT` and `MARKET`; JP market time in force is `DAY`.
- US market orders in JP support `LIMIT`, `MARKET`, `STOP_LOSS`, `STOP_LOSS_LIMIT` with `DAY` or `GTC`.
- JP stock accounts are identified by `account_type`: `CASH` or `US_MARGIN`.
- `account_tax_type` is required for JP stock `place` and `preview`; valid values are `GENERAL` and `SPECIFIC`.
- `margin_type` and `position_intent` are valid only for JP `US_MARGIN` accounts (for stock orders). For US option orders, `position_intent` is supported via `option-place`.
- `close_contracts` is JP-only and accepts up to 10 objects with `contract_id` and positive `quantity`.

### SG-Specific Notes

- Configure SG with `WEBULL_REGION_ID=sg`; sandbox uses `WEBULL_ENVIRONMENT=uat`.
- SG supports US stock/ETF trading for Singapore-based clients.
- Supported order types: `MARKET`, `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT`.
- Time in force: `DAY`, `GTC`.
- Trading sessions: `CORE`, `ALL`, `NIGHT`, `ALL_DAY`.
- SG order market is `US` only.
- No futures, crypto, options, event contracts, combo orders, or algo orders in SG region.

### TH-Specific Notes

- Configure TH with `WEBULL_REGION_ID=th`; sandbox uses `WEBULL_ENVIRONMENT=uat`.
- TH supports US stock/ETF trading for Thailand-based clients.
- Supported order types: `MARKET`, `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT`.
- Time in force: `DAY`, `GTC`.
- Trading sessions: `CORE`, `ALL`, `NIGHT`, `ALL_DAY`.
- TH order market is `US` only.
- No futures, crypto, options, event contracts, combo orders, or algo orders in TH region.

### MY-Specific Notes

- Configure MY with `WEBULL_REGION_ID=my`; sandbox uses `WEBULL_ENVIRONMENT=uat`.
- MY supports US stock/ETF trading for Malaysia-based clients.
- Supported order types: `MARKET`, `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT`.
- Time in force: `DAY`, `GTC`.
- Trading sessions: `CORE`, `ALL`, `NIGHT`, `ALL_DAY`.
- MY order market is `US` only.
- No futures, crypto, options, event contracts, combo orders, or algo orders in MY region.

### UK-Specific Notes

- Configure UK with `WEBULL_REGION_ID=uk`; sandbox uses `WEBULL_ENVIRONMENT=uat`.
- UK supports US stock/ETF trading for UK-based clients.
- Supported order types: `MARKET`, `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT`.
- Time in force: `DAY`, `GTC`.
- Trading sessions: `CORE`, `ALL`, `NIGHT`, `ALL_DAY`.
- UK order market is `US` only.
- No futures, crypto, options, event contracts, combo orders, or algo orders in UK region.

### MX-Specific Notes

- Configure MX with `WEBULL_REGION_ID=mx`; sandbox uses `WEBULL_ENVIRONMENT=uat`.
- MX supports US stock/ETF trading for Mexico-based clients.
- Supported order types: `MARKET`, `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT`.
- Time in force: `DAY`, `GTC`.
- Trading sessions: `CORE`, `ALL`, `NIGHT`, `ALL_DAY`.
- MX order market is `US` only.
- No futures, crypto, options, event contracts, combo orders, or algo orders in MX region.

### BR-Specific Notes

- Configure BR with `WEBULL_REGION_ID=br`; sandbox uses `WEBULL_ENVIRONMENT=uat`.
- BR supports US stock/ETF trading for Brazil-based clients.
- Supported order types: `MARKET`, `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT`.
- Time in force: `DAY`, `GTC`.
- Trading sessions: `CORE`, `ALL`, `NIGHT`, `ALL_DAY`.
- BR order market is `US` only.
- No futures, crypto, options, event contracts, combo orders, or algo orders in BR region.

### EU-Specific Notes

- Configure EU with `WEBULL_REGION_ID=eu`; sandbox uses `WEBULL_ENVIRONMENT=uat`.
- EU supports US stock/ETF trading for EU-based clients.
- Supported order types: `MARKET`, `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT`.
- Time in force: `DAY`, `GTC`.
- Trading sessions: `CORE`, `ALL`, `NIGHT`, `ALL_DAY`.
- EU order market is `US` only.
- No futures, crypto, options, event contracts, combo orders, or algo orders in EU region.

### ZA-Specific Notes

- Configure ZA with `WEBULL_REGION_ID=za`; sandbox uses `WEBULL_ENVIRONMENT=uat`.
- ZA supports US stock/ETF trading for South Africa-based clients.
- Supported order types: `MARKET`, `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT`.
- Time in force: `DAY`, `GTC`.
- Trading sessions: `CORE`, `ALL`, `NIGHT`, `ALL_DAY`.
- ZA order market is `US` only.
- No futures, crypto, options, event contracts, combo orders, or algo orders in ZA region.

### AU-Specific Notes

- Configure AU with `WEBULL_REGION_ID=au`; sandbox uses `WEBULL_ENVIRONMENT=uat`.
- AU supports US stock/ETF trading for Australia-based clients.
- Supported order types: `MARKET`, `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT`.
- Time in force: `DAY`, `GTC`.
- Trading sessions: `CORE`, `ALL`, `NIGHT`, `ALL_DAY`.
- AU order market is `US` only.
- No futures, crypto, options, event contracts, combo orders, or algo orders in AU region.

---

## Rate Limits

### US Region
- Market data: 600 req/min
- Order place/replace/cancel: 600 req/min
- Order query: 2 req/2s
- Auth: 10 req/30s

### HK Region
- Market data: 60 req/60s
- Order place: 15 req/s (US stocks), 1 req/s (HK/A-share)
- Order preview: 40 req/10s
- Order query: 40 req/2s

### JP Region
- Instrument lookup: 60 req/min per AppId
- Other endpoint limits follow the JP developer portal for the enabled account/API plan

### SG Region
- Market data: 300 req/60s
- Order place/replace/cancel: 600 req/60s
- Order query: 2 req/2s
- Auth: 10 req/30s

### TH Region
- Market data: 300 req/60s
- Order place/replace/cancel: 600 req/60s
- Order query: 2 req/2s
- Auth: 10 req/30s

### MY Region
- Market data: 300 req/60s
- Order place/replace/cancel: 600 req/60s
- Order query: 2 req/2s
- Auth: 10 req/30s

### UK Region
- Market data: 300 req/60s
- Order place/replace/cancel: 600 req/60s
- Order query: 2 req/2s
- Auth: 10 req/30s

### MX Region
- Market data: 300 req/60s
- Order place/replace/cancel: 600 req/60s
- Order query: 2 req/2s
- Auth: 10 req/30s

### BR Region
- Market data: 300 req/60s
- Order place/replace/cancel: 600 req/60s
- Order query: 2 req/2s
- Auth: 10 req/30s

### EU Region
- Market data: 60 req/60s
- Order place/replace/cancel: 60 req/60s
- Order query: 2 req/2s
- Auth: 10 req/30s

### ZA Region
- Market data: 60 req/60s
- Order place/replace/cancel: 60 req/60s
- Order query: 2 req/2s
- Auth: 10 req/30s

### AU Region
- Market data: 60 req/60s
- Order place/replace/cancel: 60 req/60s
- Order query: 2 req/2s
- Auth: 10 req/30s

---

## Detailed Module Documentation

- [Trading Guide](references/skill_trading.md) — Full order JSON formats, replace rules, order types, trading sessions
- [Market Data Guide](references/skill_market_data.md) — All market data actions, screener, watchlist, category values

## Official API Documentation

- US: https://developer.webull.com/apis/docs/webull-open-api-reference
- HK: https://developer.webull.hk/apis/docs/webull-open-api-reference
- JP: https://developer.webull.co.jp/apis/docs/webull-open-api-reference
- SG: https://developer.webull.com.sg/apis/docs/index.md
- TH: https://developer.webull.co.th/apis/docs/
- MY: https://developer.webull.com.my/apis/docs/
- UK: https://developer.webull-uk.com/apis/docs/
- MX: https://developer.webull.com.mx/apis/docs/
- BR: https://developer.webull.com.br/apis/docs/
- EU: https://developer.webull.eu/apis/docs/
- ZA: https://developer.webull.co.za/apis/docs/
- AU: https://developer.webull.com.au/apis/docs/

---

## Disclaimer

The information provided by this tool is for reference only and does not constitute investment advice. Trading involves risk; please make decisions carefully.
