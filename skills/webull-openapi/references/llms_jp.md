# Source: https://developer.webull.co.jp//apis/llms.txt
# Verified with:
# - https://developer.webull.co.jp/api-doc/
# - https://developer.webull.co.jp/api-doc/prepare/start
# - https://developer.webull.co.jp/api-doc/trade/trade-catalogue/
# - https://developer.webull.co.jp/api-doc/quote/get/instrument/
# Fetched: 2026-04-27

## Base URLs

### Production
- HTTP API: api.webull.co.jp
- Trading Events (gRPC): events-api.webull.co.jp

### UAT / Sandbox Examples
- HTTP API: jp-openapi-alb.uat.webullbroker.com
- Trading Events (gRPC): jp-openapi-events.uat.webullbroker.com

## Market Scope

### Supported Markets
- U.S. stocks and ETFs

### Instrument Categories
- US_STOCK
- US_ETF

## Key API Endpoints

### Market Data
- Instrument lookup
- Stock Tick, Snapshot, Quotes, Footprint, Historical Bars

### Account
- Account List
- Account Balance
- Account Positions

### Order Management
- Preview Order
- Place Order
- Replace Order
- Cancel Order
- Query Orders History
- Query Opened Orders
- Query Order Detail

### Trade Events
- Subscribe Trade Events

## JP Stock Trading Notes

### Order Markets
- US
- JP

### Order Types by Market
- JP: LIMIT, MARKET
- US: LIMIT, MARKET, STOP_LOSS, STOP_LOSS_LIMIT

### Time In Force by Market
- JP: DAY
- US: DAY, GTC, GTD

### Account Types
- CASH
- US_MARGIN

### JP Order Extension Fields
- account_tax_type: GENERAL, SPECIFIC
- margin_type: ONE_DAY, INDEFINITE
- position_intent: BUY_TO_OPEN, BUY_TO_CLOSE, SELL_TO_OPEN, SELL_TO_CLOSE
- close_contracts supported on place / preview / replace

## Reference Notes

### Quote Instrument API
- Get Instruments: /instrument/list
- Symbols required, comma-separated, up to 100 per request

### Rate Limits
- Get Instruments: 60 req/min per AppId
