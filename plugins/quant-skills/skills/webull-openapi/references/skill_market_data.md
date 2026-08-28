# Module: market-data

Real-time and historical market data for all asset classes.

## Stock

| Action | Description | Key Options |
|--------|-------------|-------------|
| `stock-snapshot` | Real-time snapshot | `--symbols AAPL,TSLA` |
| `stock-bars` | OHLCV bars (single symbol) | `--symbol AAPL --timespan D --count 200` |
| `stock-batch-bars` | OHLCV bars (multiple symbols) | `--symbols AAPL,TSLA --timespan D` |
| `stock-tick` | Tick-by-tick trades | `--symbol AAPL --count 30` |
| `stock-quotes` | Bid/ask depth | `--symbol AAPL --depth 5` |
| `stock-footprint` | Large order flow | `--symbols AAPL --timespan M1` |
| `stock-noii-bars` | NOII K-line data (auction imbalance) | `--symbol AAPL --imbalance-action-type PRE_OPEN` |
| `stock-noii-snapshot` | NOII real-time snapshot | `--symbol AAPL --imbalance-action-type PRE_CLOSE` |

### `stock-bars` / `stock-batch-bars` — Time Range Support

Both bar actions support optional time range filtering via `--start-time` and `--end-time` (Unix timestamp in **milliseconds**, long integer):

```bash
# Single symbol bars with time range
webull-skill market-data --action stock-bars --symbol AAPL --timespan D \
  --start-time 1700000000000 --end-time 1710000000000

# Batch bars with time range
webull-skill market-data --action stock-batch-bars --symbols AAPL,TSLA --timespan H1 \
  --start-time 1700000000000 --end-time 1710000000000
```

### NOII (Net Order Imbalance Indicator)

NOII data is published by NASDAQ before opening and closing auctions, providing a preview of market supply and demand.

- `--imbalance-action-type`: `PRE_OPEN` (opening auction) or `PRE_CLOSE` (closing auction)
- `stock-noii-snapshot` is only live during auction windows (9:28–9:30 AM ET and 3:50–4:00 PM ET); outside these windows, historical data is returned

```bash
# NOII K-line for opening auction
webull-skill market-data --action stock-noii-bars --symbol AAPL --imbalance-action-type PRE_OPEN

# NOII snapshot for closing auction
webull-skill market-data --action stock-noii-snapshot --symbol AAPL --imbalance-action-type PRE_CLOSE
```

## Option (US, HK, JP)

| Action | Description | Key Options |
|--------|-------------|-------------|
| `option-snapshot` | Option real-time snapshot (max 20 symbols) | `--symbols AAPL260522C00300000` |
| `option-bars` | Option OHLCV bars (batch) | `--symbols AAPL260522C00300000 --timespan D` |
| `option-tick` | Option tick-by-tick trades | `--symbol AAPL260522C00300000 --count 30` |

> **Category:** All option market data actions use `--category US_OPTION` (default).
>
> **Symbol format:** Option symbols use OCC format, e.g. `AAPL260522C00300000` (underlying + expiry + type + strike).

## Futures (US only)

| Action | Description | Key Options |
|--------|-------------|-------------|
| `futures-snapshot` | Futures snapshot | `--symbols ESM6` |
| `futures-bars` | Futures OHLCV | `--symbols ESM6 --timespan D` |
| `futures-tick` | Futures ticks | `--symbol ESM6 --count 30` |
| `futures-depth` | Order book depth | `--symbol ESM6 --depth 5` |
| `futures-footprint` | Futures order flow | `--symbols ESM6 --timespan M1` |

## Crypto (US only)

| Action | Description | Key Options |
|--------|-------------|-------------|
| `crypto-snapshot` | Crypto snapshot | `--symbols BTCUSD` |
| `crypto-bars` | Crypto OHLCV | `--symbols BTCUSD --timespan D` |

## Event Contracts (US only)

| Action | Description | Key Options |
|--------|-------------|-------------|
| `event-snapshot` | Event snapshot | `--symbols <sym>` |
| `event-depth` | Event depth | `--symbol <sym> --depth 5` |
| `event-bars` | Event OHLCV | `--symbols <sym> --timespan D` |
| `event-tick` | Event ticks | `--symbol <sym> --count 30` |

## Screener (All Regions)

| Action                  | Description                           | Key Options                                               |
|-------------------------|---------------------------------------|-----------------------------------------------------------|
| `stock-gainers-losers`       | Top gainers or losers by price change | `--rank-type DAY_1 --direction DESC`                      |
| `stock-most-active`          | Most actively traded stocks           | `--rank-type VOLUME`                                      |
| `stock-market-sectors`       | All sector overview with statistics   | `--category US_STOCK --agg-type MARKET_VALUE --period D1` |
| `stock-market-sectors-detail`| Stock list for a specific sector      | `--sector-id <id> --category US_STOCK`                    |
| `stock-high-dividend`        | High dividend yield ranking           | `--category US_STOCK --sort-by YIELD`                     |
| `stock-52-week-high-low`     | 52-week high/low ranking              | `--category US_STOCK --rank-type NEW_HIGH`                |

### `stock-gainers-losers` Options

| Option | Required | Description |
|--------|----------|-------------|
| `--rank-type` | Yes | Time period: `PRE_MARKET`, `AFTER_MARKET`, `MIN_3`, `MIN_5`, `DAY_1`, `DAY_5`, `MONTH_1`, `MONTH_3`, `WEEK_52` |
| `--category` | No | Default `US_STOCK` |
| `--sort-by` | No | Secondary sort: `CHANGE_RATIO`, `VOLUME`, `MARKET_VALUE`, `TURNOVER`, `AMPLITUDE`, etc. Default `CHANGE_RATIO` |
| `--direction` | No | `DESC` for gainers, `ASC` for losers |
| `--page-index` | No | Page number starting from 1 |
| `--page-size` | No | Records per page |

### `stock-most-active` Options

| Option | Required | Description |
|--------|----------|-------------|
| `--category` | No | Default `US_STOCK` |
| `--rank-type` | No | `VOLUME`, `RELATIVE_VOLUME_10D`, `TURNOVER`, `TURNOVER_RATE`, `AMPLITUDE`. Default `VOLUME` |
| `--sort-by` | No | Secondary sort field |
| `--direction` | No | `ASC` or `DESC`. Default `DESC` |
| `--page-index` | No | Page number starting from 1 |
| `--page-size` | No | Records per page |

### `stock-market-sectors` Options

| Option         | Required | Description                                                       |
|----------------|----------|-------------------------------------------------------------------|
| `--category`   | Yes      | Default `US_STOCK`                                                |
| `--agg-type`   | No       | Statistics type: `MARKET_VALUE`, `VOLUME`. Default `MARKET_VALUE` |
| `--period`     | No       | Statistics period: `D1`, `D5`, `M01`, `M03`. Default `D1`         |
| `--page-index` | No       | Page number starting from 1                                       |
| `--page-size`  | No       | Records per page                                                  |
| `--direction`  | No       | Sort direction: `ASC` or `DESC`                                   |

### `stock-market-sectors-detail` Options

| Option         | Required | Description                                               |
|----------------|----------|-----------------------------------------------------------|
| `--sector-id`  | Yes      | Sector ID (obtained from `stock-market-sectors` response) |
| `--category`   | Yes      | Default `US_STOCK`                                        |
| `--period`     | No       | Statistics period: `D1`, `D5`, `M01`, `M03`. Default `D1` |
| `--page-index` | No       | Page number starting from 1                               |
| `--page-size`  | No       | Records per page                                          |
| `--sort-by`    | No       | Sort field. Default `CHANGE_RATIO`                        |
| `--direction`  | No       | Sort direction: `ASC` or `DESC`                           |

### `stock-high-dividend` Options

| Option         | Required | Description                     |
|----------------|----------|---------------------------------|
| `--category`   | Yes      | Default `US_STOCK`              |
| `--sort-by`    | No       | Sort field. Default `YIELD`     |
| `--page-index` | No       | Page number starting from 1     |
| `--page-size`  | No       | Records per page                |
| `--direction`  | No       | Sort direction: `ASC` or `DESC` |

### `stock-52-week-high-low` Options

| Option         | Required | Description                                                |
|----------------|----------|------------------------------------------------------------|
| `--category`   | Yes      | Default `US_STOCK`                                         |
| `--rank-type`  | No       | Index code: `NEW_HIGH`, `NEAR_HIGH`, `NEW_LOW`, `NEAR_LOW` |
| `--sort-by`    | No       | Sort field. Default `CHANGE_RATIO_52W`                     |
| `--page-index` | No       | Page number starting from 1                                |
| `--page-size`  | No       | Records per page                                           |
| `--direction`  | No       | Sort direction: `ASC` or `DESC`                            |

```bash
# Top 20 gainers today
webull-skill market-data --action stock-gainers-losers \
  --rank-type DAY_1 --direction DESC --page-size 20

# Top losers today
webull-skill market-data --action stock-gainers-losers \
  --rank-type DAY_1 --direction ASC --page-size 20

# Most active by volume
webull-skill market-data --action stock-most-active --rank-type VOLUME

# Most active by relative volume (10-day)
webull-skill market-data --action stock-most-active --rank-type RELATIVE_VOLUME_10D
```

```bash
# Get all market sectors overview
webull-skill market-data --action stock-market-sectors --category US_STOCK --period D1

# Get stocks in a specific sector
webull-skill market-data --action stock-market-sectors-detail --sector-id 10001 --page-size 20

# High dividend stocks
webull-skill market-data --action stock-high-dividend --category US_STOCK --page-size 20

# 52-week new highs
webull-skill market-data --action stock-52-week-high-low --rank-type NEW_HIGH --direction DESC
```

## Fundamentals (All Regions)

### Stock Fundamentals

| Action | Description | Key Options |
|--------|-------------|-------------|
| `fundamentals-capital-flow` | Capital flow distribution | `--symbol AAPL --fundamental-count 5` |
| `fundamentals-industry-comparison` | Industry peer comparison (up to 20 stocks) | `--symbol AAPL --sort-by EPS_TTM` |
| `fundamentals-sec-filings` | SEC filings (US only, last 3 years) | `--symbol AAPL` |
| `fundamentals-earnings-calendar` | Earnings calendar (±6 months) | `--symbol AAPL` |
| `fundamentals-dividend-calendar` | Dividend calendar (±6 months) | `--symbol AAPL` |
| `fundamentals-forecast-eps` | Forecast EPS (last 4 actual + consensus estimate) | `--symbol AAPL` |

### Financial Statements

| Action | Description | Key Options |
|--------|-------------|-------------|
| `fundamentals-financials-indicators` | Key financial indicators | `--symbol TSLA --financial-type QUARTERLY --fundamental-count 5` |
| `fundamentals-financials-income` | Income statement | `--symbol TSLA --financial-type ANNUAL --fundamental-count 5` |
| `fundamentals-financials-cashflow` | Cashflow statement | `--symbol TSLA --financial-type QUARTERLY` |
| `fundamentals-financials-balance-sheet` | Balance sheet | `--symbol TSLA --financial-type ANNUAL` |
| `fundamentals-financials-alert` | Upcoming earnings alert | `--symbol TSLA` |

### Fund / ETF Data

| Action | Description | Key Options |
|--------|-------------|-------------|
| `fundamentals-fund-brief` | Fund brief information | `--symbol QQQ` |
| `fundamentals-fund-allocation` | Fund asset allocation | `--symbol QQQ` |
| `fundamentals-fund-holdings` | Fund top 10 holdings | `--symbol QQQ` |
| `fundamentals-fund-performance` | Fund performance | `--symbol QQQ` |
| `fundamentals-fund-rating` | Fund rating | `--symbol QQQ` |
| `fundamentals-fund-net-value` | Fund net value history | `--symbol QQQ --last-date 2026-04-01 --fundamental-count 10` |
| `fundamentals-fund-dividends` | Fund dividend history | `--symbol QQQ --page-index 1 --page-size 10` |
| `fundamentals-fund-splits` | Fund split history | `--symbol QQQ` |
| `fundamentals-fund-files` | Fund documents/files | `--symbol QQQ` |

### Fundamentals Common Options

| Option | Required | Description |
|--------|----------|-------------|
| `--symbol` | Yes | Security symbol, e.g. AAPL, QQQ |
| `--category` | No | Default `US_STOCK`. Supported varies by action (see below) |
| `--fundamental-count` | No | Number of records (default: API default of 5, max 20) |
| `--financial-type` | No | `ANNUAL` or `QUARTERLY` (default `QUARTERLY`). For financial statement actions only |
| `--last-date` | No | Last query date for fund-net-value, e.g. `2026-04-01` |
| `--sort-by` | No | Sort field for industry-comparison. Values: `EPS_TTM`, `NAPS`, `DPS_TTM`, `ROE`, `DEBT_TO_ASSETS`, `NET_MARGIN`, `DIV_YIELD_TTM`, `PE_TTM`, `PB_RATIO` |

```bash
# Capital flow for AAPL (last 3 records)
webull-skill market-data --action fundamentals-capital-flow --symbol AAPL --fundamental-count 3

# Industry comparison sorted by PE ratio
webull-skill market-data --action fundamentals-industry-comparison --symbol AAPL --sort-by PE_TTM

# SEC filings
webull-skill market-data --action fundamentals-sec-filings --symbol AAPL

# Earnings calendar
webull-skill market-data --action fundamentals-earnings-calendar --symbol TSLA

# Dividend calendar
webull-skill market-data --action fundamentals-dividend-calendar --symbol AAPL

# Forecast EPS (last 4 quarters actual + next quarter estimate)
webull-skill market-data --action fundamentals-forecast-eps --symbol AAPL

# Quarterly income statement (last 4 quarters)
webull-skill market-data --action fundamentals-financials-income --symbol TSLA \
  --financial-type QUARTERLY --fundamental-count 4

# Annual balance sheet
webull-skill market-data --action fundamentals-financials-balance-sheet --symbol AAPL \
  --financial-type ANNUAL --fundamental-count 5

# Fund brief
webull-skill market-data --action fundamentals-fund-brief --symbol QQQ

# Fund top holdings
webull-skill market-data --action fundamentals-fund-holdings --symbol SPY

# Fund net value (paginated by date)
webull-skill market-data --action fundamentals-fund-net-value --symbol QQQ \
  --last-date 2026-04-01 --fundamental-count 10

# Fund dividends
webull-skill market-data --action fundamentals-fund-dividends --symbol QQQ --page-size 10
```

## Watchlist (US, HK, JP)

Watchlist operations manage saved lists of instruments. Maximum 20 watchlists, 1000 instruments total across all watchlists. Does not support futures, options, or event contracts.

- US region: supports US stocks and HK stocks
- HK region: supports HK stocks and US stocks
- JP region: supports US stocks

| Action | Description | Key Options |
|--------|-------------|-------------|
| `watchlist-list` | Get all watchlists | |
| `watchlist-create` | Create a new watchlist | `--watchlist-name <name>` |
| `watchlist-delete` | Delete a watchlist | `--watchlist-id <id>` |
| `watchlist-update` | Update watchlist name or sort | `--watchlist-id <id> --watchlist-name <name>` |
| `watchlist-instruments-list` | Get instruments in a watchlist | `--watchlist-id <id>` |
| `watchlist-instruments-add` | Add instruments to a watchlist | `--watchlist-id <id> --instruments-json '[...]'` |
| `watchlist-instruments-remove` | Remove instruments from a watchlist | `--watchlist-id <id> --instruments-json '[...]'` |
| `watchlist-instruments-update` | Update instrument sort order | `--watchlist-id <id> --instruments-json '[...]'` |

### `--instruments-json` Format

Pass a JSON array of instrument objects. Fields vary by operation:

| Operation | Required Fields | Optional Fields |
|-----------|----------------|-----------------|
| `add` | `symbol`, `category` | `sort` |
| `remove` | `symbol`, `category` | |
| `update` | `symbol`, `category`, `sort` | |

```bash
# List all watchlists
webull-skill market-data --action watchlist-list

# Create a watchlist
webull-skill market-data --action watchlist-create --watchlist-name "My Tech Stocks"

# Add instruments (use --instruments-json)
webull-skill market-data --action watchlist-instruments-add \
  --watchlist-id <id> \
  --instruments-json '[{"symbol":"AAPL","category":"US_STOCK","sort":1},{"symbol":"TSLA","category":"US_STOCK","sort":2}]'

# Remove instruments
webull-skill market-data --action watchlist-instruments-remove \
  --watchlist-id <id> \
  --instruments-json '[{"symbol":"AAPL","category":"US_STOCK"}]'

# Delete a watchlist
webull-skill market-data --action watchlist-delete --watchlist-id <id>
```

## Common Options

| Option | Default | Description |
|--------|---------|-------------|
| `--category` | auto | See [Category Values](#category-values) below |
| `--timespan` | `D` | `M1`, `M5`, `M15`, `M30`, `H1`, `H4`, `D`, `W` |
| `--count` | `200` | Number of bars/ticks |
| `--depth` | `1` | Order book depth levels |
| `--extend-hour-required` | false | Include extended hours |
| `--overnight-required` | false | Include overnight data |
| `--start-time` | (none) | Start timestamp in milliseconds (Long), for bar actions |
| `--end-time` | (none) | End timestamp in milliseconds (Long), for bar actions |
| `--imbalance-action-type` | `PRE_OPEN` | NOII type: `PRE_OPEN` or `PRE_CLOSE` |

## Category Values

Category determines which market's data you're querying. It varies by region:

**US Region (`WEBULL_REGION_ID=us`):**

| Category | Description |
|----------|-------------|
| `US_STOCK` | US stocks (default for stock actions) |
| `US_ETF` | US ETFs |
| `US_FUTURES` | US futures (default for futures actions) |
| `US_CRYPTO` | US crypto (default for crypto actions) |
| `US_EVENT` | US event contracts (default for event actions) |

**HK Region (`WEBULL_REGION_ID=hk`):**

| Category | Description |
|----------|-------------|
| `US_STOCK` | US stocks (traded via HK account) |
| `US_ETF` | US ETFs (traded via HK account) |
| `HK_STOCK` | Hong Kong stocks |
| `CN_STOCK` | China Connect A-shares |

**JP Region (`WEBULL_REGION_ID=jp`):**

| Category | Description |
|----------|-------------|
| `US_STOCK` | US stocks (traded via JP account) |
| `US_ETF` | US ETFs (traded via JP account) |

**SG Region (`WEBULL_REGION_ID=sg`):**

| Category | Description |
|----------|-------------|
| `US_STOCK` | US stocks (traded via SG account) |
| `US_ETF` | US ETFs (traded via SG account) |

**EU Region (`WEBULL_REGION_ID=eu`):**

| Category | Description |
|----------|-------------|
| `US_STOCK` | US stocks (traded via EU account) |
| `US_ETF` | US ETFs (traded via EU account) |

**ZA Region (`WEBULL_REGION_ID=za`):**

| Category | Description |
|----------|-------------|
| `US_STOCK` | US stocks (traded via ZA account) |
| `US_ETF` | US ETFs (traded via ZA account) |

**AU Region (`WEBULL_REGION_ID=au`):**

| Category | Description |
|----------|-------------|
| `US_STOCK` | US stocks (traded via AU account) |
| `US_ETF` | US ETFs (traded via AU account) |

Examples:
```bash
# US stock (default for US region)
webull-skill market-data --action stock-snapshot --symbols AAPL

# HK stock (must specify category for HK region)
webull-skill market-data --action stock-snapshot --symbols 00700 --category HK_STOCK

# China Connect A-share
webull-skill market-data --action stock-snapshot --symbols 600519 --category CN_STOCK

# JP region US stock
WEBULL_REGION_ID=jp webull-skill market-data --action stock-snapshot --symbols AAPL --category US_STOCK
```
