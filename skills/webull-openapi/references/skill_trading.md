# Module: trading

Instrument queries, account/asset operations, and all order operations.

## Instrument Queries

| Action | Description | Key Options |
|--------|-------------|-------------|
| `instrument-stock` | Stock/ETF instrument info | `--symbols AAPL,TSLA` |
| `instrument-crypto` | Crypto instrument info | `--symbols BTCUSD` |
| `instrument-futures-products` | Futures product codes | `--category US_FUTURES` |
| `instrument-futures-product-class` | Futures product classification groups | `--category US_FUTURES` |
| `instrument-futures-list` | Futures instruments by symbol | `--symbols ESM6` |
| `instrument-futures-by-code` | Futures by product code | `--code ES` |
| `instrument-event-series` | Event contract series | `--page-size 50` |
| `instrument-event-list` | Event instruments by series | `--series-symbol <sym>` |
| `instrument-event-categories` | Event contract categories | |
| `instrument-event-events` | Events within a series | `--series-symbol <sym>` |
| `instrument-option-contracts` | Option contract list by underlying symbols | `--symbols AAPL --category US_OPTION` |

## Instrument Fundamentals (US, HK, JP)

| Action | Description | Key Options |
|--------|-------------|-------------|
| `instrument-company-profile` | Company profile (description, CEO, sector, etc.) | `--symbol AAPL` |
| `instrument-analyst-rating` | Analyst buy/hold/sell rating counts | `--symbol AAPL` |
| `instrument-analyst-target-price` | Analyst target price (mean/high/low/median) | `--symbol AAPL` |

```bash
# Get company profile
webull-skill trading --action instrument-company-profile --symbol AAPL

# Get analyst rating
webull-skill trading --action instrument-analyst-rating --symbol TSLA

# Get analyst target price
webull-skill trading --action instrument-analyst-target-price --symbol NVDA
```

## Account & Asset

| Action | Description | Key Options |
|--------|-------------|-------------|
| `account-list` | List all linked accounts | |
| `balance` | Account balance | `--account-id <id>` |
| `position` | Account positions | `--account-id <id>` |
| `position-detail` | Position details by instrument (JP only) | `--account-id <id> --instrument-id <id>` |

## Stock Orders

> **⚠️ Action routing by asset type:**
> - **Stock/ETF** → use `place`, `preview`, `replace`
> - **Option** → use `option-place`, `option-preview`, `option-replace`, `option-strategy-place`
> - **Futures** → use `futures-place`, `futures-replace`
> - **Crypto** → use `crypto-place`
> - **Event Contract** → use `event-place`, `event-replace`
>
> Do NOT use `place` for option/futures/crypto/event orders. Each asset type has its own dedicated action.

| Action | Description |
|--------|-------------|
| `place` | Place stock/ETF order (single, non-combo) |
| `preview` | Preview stock/ETF order without submitting |
| `replace` | Modify existing stock/ETF order |
| `batch-place` | Combo orders (OTO/OCO/OTOCO) — US only |
| `algo-place` | Algorithmic order (TWAP/VWAP/POV) — US only |

## Option Orders

> **Use these actions for ALL option trading.** Do NOT use the stock `place` action for options.

| Action | Description |
|--------|-------------|
| `option-place` | Place single-leg option order |
| `option-preview` | Preview option order |
| `option-replace` | Modify option order |
| `option-strategy-place` | Multi-leg strategy (VERTICAL, STRADDLE, etc.) — US only |

## Futures / Crypto / Event Orders (US only)

| Action | Description |
|--------|-------------|
| `futures-place` | Place futures order |
| `futures-preview` | Preview futures order without submitting |
| `futures-replace` | Modify futures order |
| `crypto-place` | Place crypto order (no replace supported) |
| `event-place` | Place event contract order |
| `event-replace` | Modify event contract order |

## Order Management

| Action | Description | Key Options |
|--------|-------------|-------------|
| `cancel` | Cancel an order | `--account-id`, `--client-order-id` |
| `open` | List open/pending orders | `--account-id` |
| `history` | Order history | `--account-id` |
| `detail` | Single order detail | `--account-id`, `--client-order-id` |
| `local-check` | Risk check only (no API call) | `--order-json` |

---

## Order JSON Format

Orders are passed via `--order-json` (inline string) or `--order-file` (path to a JSON file). **`--order-file` is strongly recommended** to avoid shell quoting issues.

> **Important:** The `place` and `replace` actions accept **different** JSON fields. Do NOT use `place` fields for `replace` — the CLI spreads JSON keys directly into the function, so unexpected fields cause errors.

> **`client_order_id` / `client_combo_order_id` rules:** Max 32 characters, must be alphanumeric only (letters and digits, no hyphens/underscores/special chars), and must be unique per account. If not provided, the system auto-generates one.

---

### Place Order JSON (for `place`, `preview`)

> **Action scope:** The `place` action is for **stock/equity orders only**. For option orders use `option-place`, for futures use `futures-place`, for crypto use `crypto-place`, for event contracts use `event-place`.

> **Type note:** Stock place CLI does `float()` conversion internally, so strings technically work — but for consistency and to avoid issues, always use **number** types for numeric fields.

| Field | Required | JSON Type | Values / Description |
|-------|----------|-----------|----------------------|
| `combo_type` | Yes | string | `NORMAL` (single order). For combo: `MASTER`, `STOP_PROFIT`, `STOP_LOSS`, `OTO`, `OCO`, `OTOCO` |
| `symbol` | Yes | string | Ticker symbol, e.g. `AAPL`, `00700`, `BTCUSD`, `ESZ5` |
| `instrument_type` | Yes | string | `EQUITY`, `OPTION`, `FUTURES`, `CRYPTO`, `EVENT` |
| `market` | Yes | string | Region-dependent: US region `US`; HK region `US`, `HK`, `CN`; JP region `US`, `JP`; SG region `US` |
| `side` | Yes | string | `BUY`, `SELL`, `SHORT` |
| `order_type` | Yes | string | See [Order Types by Market](#order-types-by-market) below |
| `time_in_force` | Yes | string | See [Time in Force](#time-in-force) below |
| `quantity` | Conditional | number (float) | Number of shares/contracts. Required when `entrust_type=QTY`. e.g. `10` — NOT `"10"` |
| `entrust_type` | Yes | string | `QTY` (by quantity) or `AMOUNT` (fractional shares / crypto by dollar amount) |
| `limit_price` | Conditional | number (float) | Required for `LIMIT`, `STOP_LOSS_LIMIT` orders, e.g. `180` — NOT `"180"` |
| `stop_price` | Conditional | number (float) | Required for `STOP_LOSS`, `STOP_LOSS_LIMIT` orders |
| `support_trading_session` | Region-dependent stock orders | string | Trading session. See [Trading Sessions](#trading-sessions) below |
| `total_cash_amount` | Conditional | number (float) | Required when `entrust_type=AMOUNT` (US fractional shares / crypto) |
| `trailing_type` | Conditional | string | Required for `TRAILING_STOP_LOSS`: `AMOUNT` or `PERCENTAGE` |
| `trailing_stop_step` | Conditional | number (float) | Required for `TRAILING_STOP_LOSS`: trail amount or percentage (0.01 = 1%) |
| `sender_sub_id` | No (HK broker) | string | Broker user UUID for third-party transactions (HK region, institutional only) |
| `no_party_ids` | No (HK broker) | array | BCAN party identifiers for HK stock orders (institutional only). See below |
| `account_tax_type` | JP stock orders | string | JP-only. Required for JP stock `place` / `preview`. Values: `GENERAL`, `SPECIFIC` |
| `margin_type` | JP margin account only | string | JP-only. `US_MARGIN` accounts only. Values: `ONE_DAY`, `INDEFINITE` |
| `position_intent` | JP margin account only | string | For stock orders: JP-only, `US_MARGIN` accounts only. For option orders, use `option-place` instead (US only). Values: `BUY_TO_OPEN`, `BUY_TO_CLOSE`, `SELL_TO_OPEN`, `SELL_TO_CLOSE` |
| `close_contracts` | No (JP only) | array | JP-only close payload. Max 10 `{ "contract_id": "...", "quantity": ... }` items |

> **`quantity` vs `total_cash_amount`:** These two fields are mutually exclusive.
> - When `entrust_type=QTY`: provide `quantity` (number of shares/contracts)
> - When `entrust_type=AMOUNT`: provide `total_cash_amount` (dollar amount for fractional shares / crypto)
> - Do NOT provide both at the same time.

Stock limit buy example:
```json
{
  "symbol": "AAPL",
  "side": "BUY",
  "order_type": "LIMIT",
  "limit_price": 180,
  "quantity": 10,
  "instrument_type": "EQUITY",
  "market": "US",
  "time_in_force": "DAY",
  "entrust_type": "QTY",
  "support_trading_session": "CORE",
  "combo_type": "NORMAL"
}
```

HK stock order example (with BCAN, institutional/broker only):
```json
{
  "symbol": "00700",
  "side": "BUY",
  "order_type": "ENHANCED_LIMIT",
  "limit_price": 350,
  "quantity": 100,
  "instrument_type": "EQUITY",
  "market": "HK",
  "time_in_force": "DAY",
  "entrust_type": "QTY",
  "combo_type": "NORMAL",
  "sender_sub_id": "<broker_user_uuid>",
  "no_party_ids": [
    {
      "party_id": "ABC123.2568",
      "party_id_source": "D",
      "party_role": "3"
    }
  ]
}
```

`no_party_ids` array item fields:

| Field | Required | Description |
|-------|----------|-------------|
| `party_id` | Yes | BCAN ID, format: `CE_NUMBER.BCAN` e.g. `ABC123.2568` |
| `party_id_source` | Yes | Always `"D"` (Proprietary/Custom Code) |
| `party_role` | Yes | Always `"3"` (Client ID / BCAN Field) |

JP stock order example:
```json
{
  "symbol": "AAPL",
  "side": "BUY",
  "order_type": "LIMIT",
  "limit_price": 180,
  "quantity": 10,
  "instrument_type": "EQUITY",
  "market": "US",
  "time_in_force": "DAY",
  "entrust_type": "QTY",
  "support_trading_session": "CORE",
  "combo_type": "NORMAL",
  "account_tax_type": "GENERAL"
}
```

JP margin-account example:
```json
{
  "symbol": "AAPL",
  "side": "BUY",
  "order_type": "LIMIT",
  "limit_price": 180,
  "quantity": 10,
  "instrument_type": "EQUITY",
  "market": "US",
  "time_in_force": "DAY",
  "entrust_type": "QTY",
  "support_trading_session": "CORE",
  "combo_type": "NORMAL",
  "account_tax_type": "GENERAL",
  "margin_type": "ONE_DAY",
  "position_intent": "BUY_TO_OPEN"
}
```

---

### Option Place JSON (for `option-place`, `option-preview`)

> **⚠️ Type-sensitive:** Option place uses `**o` spread — JSON types must match function signatures exactly. `quantity` must be **integer**, `strike_price`/`limit_price`/`stop_price` must be **number** (float), not strings.

| Field | Required | JSON Type | Values / Description |
|-------|----------|-----------|----------------------|
| `symbol` | Yes | string | Underlying symbol, e.g. `AAPL` |
| `instrument_type` | Yes | string | `OPTION` |
| `option_type` | Yes | string | `CALL` or `PUT` |
| `strike_price` | Yes | number (float) | Strike price, e.g. `220.00` — NOT `"220.00"` |
| `expiration_date` | Yes | string | Expiration date, format `yyyy-MM-dd`, e.g. `"2026-06-19"` |
| `side` | Yes | string | `BUY`, `SELL`, `SHORT` |
| `order_type` | Yes | string | `MARKET`, `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT` |
| `time_in_force` | Yes | string | `DAY`, `GTC`. Sell-side only supports `DAY` |
| `quantity` | Yes | number (int) | Number of contracts, e.g. `1` — NOT `"1"` |
| `limit_price` | Conditional | number (float) | Required for `LIMIT` orders, e.g. `11.25` — NOT `"11.25"` |
| `stop_price` | Conditional | number (float) | Required for `STOP_LOSS` orders |
| `position_intent` | No | string | Position strategy (US only). `BUY_TO_OPEN`, `BUY_TO_CLOSE`, `SELL_TO_OPEN`, `SELL_TO_CLOSE`. Must match `side`. For combo orders, only set on the MASTER order |
| `sender_sub_id` | No (HK broker) | string | Broker user UUID (HK region, institutional only). No BCAN needed for options |

Option single-leg example:
```json
{
  "symbol": "AAPL",
  "instrument_type": "OPTION",
  "option_type": "CALL",
  "strike_price": 220.00,
  "expiration_date": "2026-06-19",
  "side": "BUY",
  "order_type": "LIMIT",
  "limit_price": 11.25,
  "quantity": 1,
  "time_in_force": "DAY",
  "position_intent": "BUY_TO_OPEN"
}
```

---

### Option Strategy Place JSON (for `option-strategy-place`)

> **⚠️ Type-sensitive:** Same as option-place — numeric fields must be numbers, not strings.

| Field | Required | JSON Type | Values / Description |
|-------|----------|-----------|----------------------|
| `strategy` | Yes | string | `VERTICAL`, `STRADDLE`, `STRANGLE`, `BUTTERFLY`, `CONDOR`, `CALENDAR`, `DIAGONAL`, `IRON_BUTTERFLY`, `IRON_CONDOR`, `COLLAR_WITH_STOCK`, `COVERED_STOCK` |
| `symbol` | Yes | string | Underlying symbol |
| `order_type` | Yes | string | `LIMIT`, `MARKET` |
| `time_in_force` | Yes | string | `DAY`, `GTC` |
| `quantity` | No | number (int) | Number of contracts per leg |
| `limit_price` | Conditional | number (float) | Net debit/credit price for the strategy |
| `legs` | Yes | array | Array of leg objects (see below) |

Each leg object:

| Field | Required | JSON Type | Values |
|-------|----------|-----------|--------|
| `side` | Yes | string | `BUY`, `SELL` |
| `quantity` | Yes | string | Contracts for this leg |
| `symbol` | Yes | string | Underlying symbol |
| `strike_price` | Yes | string | Strike price |
| `option_expire_date` | Yes | string | `yyyy-MM-dd` |
| `instrument_type` | Yes | string | `OPTION` |
| `option_type` | Yes | string | `CALL` or `PUT` |
| `market` | Yes | string | `US` |

---

### Futures Place JSON (for `futures-place`)

> **⚠️ Type-sensitive:** Futures place uses `**o` spread — `quantity`/`limit_price`/`stop_price` must be **number** (float), not strings.

| Field | Required | JSON Type | Values / Description |
|-------|----------|-----------|----------------------|
| `symbol` | Yes | string | Futures symbol, e.g. `ESZ5`, `NQM6` |
| `side` | Yes | string | `BUY`, `SELL` |
| `order_type` | Yes | string | `MARKET`, `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT`, `TRAILING_STOP_LOSS` |
| `time_in_force` | Yes | string | `DAY`, `GTC` |
| `quantity` | Yes | number (float) | Number of contracts, e.g. `1` — NOT `"1"` |
| `limit_price` | Conditional | number (float) | Required for `LIMIT`, `STOP_LOSS_LIMIT` |
| `stop_price` | Conditional | number (float) | Required for `STOP_LOSS`, `STOP_LOSS_LIMIT` |

Futures example:
```json
{
  "symbol": "ESZ5",
  "side": "BUY",
  "order_type": "LIMIT",
  "limit_price": 4500,
  "quantity": 1,
  "time_in_force": "DAY"
}
```

---

### Crypto Place JSON (for `crypto-place`)

> **⚠️ Type-sensitive:** Crypto place uses `**o` spread — `quantity`/`limit_price`/`stop_price`/`total_cash_amount` must be **number** (float), not strings.

| Field | Required | JSON Type | Values / Description |
|-------|----------|-----------|----------------------|
| `symbol` | Yes | string | e.g. `BTCUSD`, `ETHUSD` |
| `side` | Yes | string | `BUY`, `SELL` |
| `order_type` | Yes | string | `MARKET` (tif **must** be `IOC`), `LIMIT` (tif `DAY`/`GTC`), `STOP_LOSS_LIMIT` (tif `DAY`/`GTC`) |
| `time_in_force` | Yes | string | `IOC` (only for `MARKET`), `DAY` or `GTC` (for `LIMIT`/`STOP_LOSS_LIMIT`) |
| `entrust_type` | Yes | string | `QTY` or `AMOUNT` |
| `quantity` | Conditional | number (float) | Required when `entrust_type=QTY`. Supports up to 8 decimal places |
| `total_cash_amount` | Conditional | number (float) | Required when `entrust_type=AMOUNT` |
| `limit_price` | Conditional | number (float) | Required for `LIMIT`, `STOP_LOSS_LIMIT` |
| `stop_price` | Conditional | number (float) | Required for `STOP_LOSS_LIMIT` |

> Note: Crypto does NOT support replace (modify) orders. When selling, position must not fall below $2.

Crypto example:
```json
{
  "symbol": "BTCUSD",
  "side": "BUY",
  "order_type": "LIMIT",
  "limit_price": 80000,
  "quantity": 0.003,
  "time_in_force": "DAY",
  "entrust_type": "QTY"
}
```

---

### Event Contract Place JSON (for `event-place`)

> **⚠️ Type-sensitive:** Event place uses `**o` spread — `quantity` and `limit_price` must be **number** (float), not strings.

| Field | Required | JSON Type | Values / Description |
|-------|----------|-----------|----------------------|
| `symbol` | Yes | string | Event contract symbol |
| `side` | Yes | string | `BUY`, `SELL` |
| `quantity` | Yes | number (float) | Number of contracts. Accepts 0-2 decimal places |
| `limit_price` | Yes | number (float) | Limit price (LIMIT orders only) |
| `event_outcome` | Yes | string | `yes` or `no` |
| `order_type` | No | string | Default `LIMIT` (only LIMIT supported) |
| `time_in_force` | No | string | Default `DAY` (only DAY supported) |

Event contract example:
```json
{
  "symbol": "KXRATECUTCOUNT-26DEC31-T3",
  "side": "BUY",
  "quantity": 5,
  "limit_price": 0.10,
  "event_outcome": "yes"
}
```

---

### Algo Place JSON (for `algo-place`) — US only

> **⚠️ Type-sensitive:** Algo place uses `**o` spread — `quantity`/`limit_price` must be **number**, `target_vol_percent`/`max_target_percent` must be **integer**.

| Field | Required | JSON Type | Values / Description |
|-------|----------|-----------|----------------------|
| `symbol` | Yes | string | Stock symbol |
| `side` | Yes | string | `BUY`, `SELL` |
| `quantity` | Yes | number (float) | Number of shares |
| `algo_type` | Yes | string | `TWAP`, `VWAP`, `POV` |
| `order_type` | No | string | `MARKET` or `LIMIT` (default `LIMIT`) |
| `limit_price` | Conditional | number (float) | Required for `LIMIT` order type |
| `max_target_percent` | Conditional | number (int) | Required for `TWAP`/`VWAP`. Integer 1-20 |
| `target_vol_percent` | Conditional | number (int) | Required for `POV`. Integer 1-20 |
| `algo_start_time` | No | string | US Eastern Time, `HH:mm:ss` format, e.g. `"09:30:00"` |
| `algo_end_time` | No | string | US Eastern Time, `HH:mm:ss` format, e.g. `"16:00:00"` |

Algo TWAP example:
```json
{
  "symbol": "AAPL",
  "side": "BUY",
  "quantity": 100,
  "algo_type": "TWAP",
  "order_type": "LIMIT",
  "limit_price": 180,
  "max_target_percent": 10,
  "algo_start_time": "09:30:00",
  "algo_end_time": "16:00:00"
}
```

---

## Replace (Modify) Order JSON

Replace actions use a **different, smaller** set of fields. Only include `client_order_id` plus the fields you want to change.

> **CRITICAL:** Do NOT include `symbol`, `side`, `instrument_type`, `market`, `entrust_type`, or `combo_type` in replace JSON — these cause `unexpected keyword argument` errors.

> **Note:** `client_order_id` MUST be in the JSON body. The `--client-order-id` CLI flag is NOT passed to replace functions.

### Stock Replace (`replace`)

| Field | Required | JSON Type | Description |
|-------|----------|-----------|-------------|
| `client_order_id` | Yes | string | The order to modify |
| `quantity` | No | number (float) | New quantity |
| `limit_price` | No | number (float) | New limit price |
| `stop_price` | No | number (float) | New stop price |
| `time_in_force` | No | string | `DAY`, `GTC` |
| `order_type` | No | string | New order type |
| `trailing_type` | No | string | `AMOUNT` or `PERCENTAGE` |
| `trailing_stop_step` | No | number (float) | New trailing stop spread |
| `target_vol_percent` | No | number (int) | For algo orders (1-20) |
| `max_target_percent` | No | number (int) | For algo orders (1-20) |
| `algo_start_time` | No | string | For algo orders, `HH:mm:ss` |
| `algo_end_time` | No | string | For algo orders, `HH:mm:ss` |
| `close_contracts` | JP conditional | array | JP-only close payload. Required on replace if the original order used `close_contracts` |

JP `close_contracts` replace rules:

- If the original JP stock order contains `close_contracts`, every replace request for that order must include `close_contracts`.
- The `close_contracts` structure must remain the same as the original order.
- The `close_contracts` array length must remain the same as the original order.
- Each item's `contract_id` must remain exactly the same as the original order.
- If `close_contracts` is modified, only each item's internal `quantity` may be changed.
- `close_contracts` can contain at most 10 contracts.
- If `contract_id` is not passed on an original close order, backend closes by first-in-first-out. If a contract-level close order did pass `contract_id`, preserve it during replace.

`close_contracts` item fields:

| Field | Required | JSON Type | Description |
|-------|----------|-----------|-------------|
| `contract_id` | Yes | string | Contract ID from the original order |
| `quantity` | Yes | string | Quantity to close under this contract ID, e.g. `"10"` |

Stock replace example — change quantity from 1 to 2:
```json
{
  "client_order_id": "7af9c5c03a6f4e6ca46a194609f158e1",
  "quantity": 2,
  "limit_price": 258
}
```

JP stock replace example with `close_contracts`:
```json
{
  "client_order_id": "7af9c5c03a6f4e6ca46a194609f158e1",
  "quantity": 2,
  "close_contracts": [
    {
      "contract_id": "contract-1",
      "quantity": "2"
    }
  ]
}
```

Replace example using `--order-file` (recommended):
```bash
echo '{"client_order_id":"<oid>","quantity":2}' > /tmp/replace.json
webull-skill trading --action replace --account-id <id> --order-file /tmp/replace.json
```

### Option Replace (`option-replace`)

> **⚠️ Type-sensitive:** Option replace requires `quantity` as **integer** (not string) and `limit_price`/`stop_price` as **number** (not string). Passing `"2"` instead of `2` will cause errors.

| Field | Required | JSON Type | Description |
|-------|----------|-----------|-------------|
| `client_order_id` | Yes | string | The order to modify |
| `quantity` | No | number (int) | New quantity — must be integer, NOT string |
| `limit_price` | No | number (float) | New limit price — must be number, NOT string |
| `stop_price` | No | number (float) | New stop price — must be number, NOT string |
| `time_in_force` | No | string | `DAY`, `GTC` |

Option replace example:
```json
{
  "client_order_id": "abc123def456",
  "quantity": 2,
  "limit_price": 3.5
}
```

> Note: Option leg IDs are auto-fetched from order detail. No need to provide `legs` manually.

### Futures Replace (`futures-replace`)

Futures modification rules (from official API docs):
- Market orders: only `quantity` can be modified
- Limit orders: `order_type` (can only change to `MARKET`), `time_in_force`, `quantity`, `limit_price`
- Stop orders: `order_type` (can only change to `MARKET`), `time_in_force`, `quantity`, `stop_price`
- Stop limit orders: `order_type` (can only change to `LIMIT`), `time_in_force`, `quantity`, `limit_price`, `stop_price`
- Trailing stop orders: only `trailing_stop_step` can be modified

| Field | Required | JSON Type | Description |
|-------|----------|-----------|-------------|
| `client_order_id` | Yes | string | The order to modify |
| `quantity` | No | number (float) | New quantity |
| `limit_price` | No | number (float) | New limit price |
| `order_type` | No | string | New order type (restricted, see rules above) |

Futures replace example:
```json
{
  "client_order_id": "abc123def456",
  "quantity": 2,
  "limit_price": 4550
}
```

### Event Replace (`event-replace`)

| Field | Required | JSON Type | Description |
|-------|----------|-----------|-------------|
| `client_order_id` | Yes | string | The order to modify |
| `quantity` | No | number (float) | New quantity |
| `limit_price` | No | number (float) | New limit price |

Event replace example:
```json
{
  "client_order_id": "abc123def456",
  "quantity": 10,
  "limit_price": 0.15
}
```

### Crypto Replace

**Not supported.** Cancel and re-place instead.

---

## Order Types by Market

| Market | Supported Order Types |
|--------|----------------------|
| US stocks/ETFs | `MARKET`, `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT`, `TRAILING_STOP_LOSS` |
| US stocks (institutional) | Also: `MARKET_ON_OPEN`, `MARKET_ON_CLOSE`, `LIMIT_ON_OPEN` |
| US options | `MARKET`, `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT` |
| US futures | `MARKET`, `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT`, `TRAILING_STOP_LOSS` |
| US crypto | `MARKET`, `LIMIT`, `STOP_LOSS_LIMIT` |
| US event contracts | `LIMIT` only |
| HK stocks | `ENHANCED_LIMIT`, `AT_AUCTION`, `AT_AUCTION_LIMIT` |
| CN A-shares (via HK) | `LIMIT` only |

## Time in Force

| Value | Description | Supported By |
|-------|-------------|--------------|
| `DAY` | Valid for current trading day only | All instruments |
| `GTC` | Good-Till-Canceled (up to 60 days) | US stocks, options, futures, crypto |
| `IOC` | Immediate-Or-Cancel (unfilled portion canceled) | Crypto `MARKET` orders only |

## Trading Sessions

Natural language "trading session" maps to the order JSON field `support_trading_session`.

| Value | Description | Supported Regions |
|-------|-------------|-------------------|
| `CORE` | Regular hours (9:30 AM - 4:00 PM ET) | US, HK, JP, SG, TH, MY, UK, MX, BR, EU, ZA, AU |
| `ALL` | Extended hours (pre-market + after-hours) | US, HK, JP, SG, TH, MY, UK, MX, BR, EU, ZA, AU |
| `NIGHT` | Night session only | US, HK, JP, SG, TH, MY, UK, MX, BR, EU, ZA, AU |
| `ALL_DAY` | Included overnight hours, 8:00 p.m. ET - 8:00 p.m. ET the next day | HK, JP, SG, TH, MY, UK, MX, BR, EU, ZA, AU |

## Combo Types (US stocks only)

| Value | Description |
|-------|-------------|
| `NORMAL` | Standard single order |
| `MASTER` | Simple order + take profit or stop loss |
| `STOP_PROFIT` | Take profit order (child of MASTER) |
| `STOP_LOSS` | Stop loss order (child of MASTER) |
| `OTO` | One Triggers Other |
| `OCO` | One Cancels Other |
| `OTOCO` | One Triggers a One Cancels Other |

## Option Strategies (US only)

`SINGLE`, `COVERED_STOCK`, `VERTICAL`, `STRADDLE`, `STRANGLE`, `CALENDAR`, `DIAGONAL`, `BUTTERFLY`, `CONDOR`, `COLLAR_WITH_STOCK`, `IRON_BUTTERFLY`, `IRON_CONDOR`

## Algo Types (US only)

| Type | Description | Required Param |
|------|-------------|----------------|
| `TWAP` | Time Weighted Average Price | `max_target_percent` (1-20) |
| `VWAP` | Volume Weighted Average Price | `max_target_percent` (1-20) |
| `POV` | Percentage of Volume | `target_vol_percent` (1-20) |
