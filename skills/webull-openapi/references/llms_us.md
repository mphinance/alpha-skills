# Source: https://developer.webull.com/apis/llms.txt
# Fetched: 2026-04-07

## Base URLs

### Production Environment
- HTTP API: api.webull.com
- Trading message push: events-api.webull.com
- Market data message push: data-api.webull.com

### Test Environment
- HTTP API: api.sandbox.webull.com
- Trading message push: events-api.sandbox.webull.com

## Key API Endpoints

### Market Data - Stock
- Stock Tick, Snapshot, Quotes, Footprint, Historical Bars (batch + single)

### Market Data - Futures
- Futures Tick, Snapshot, Footprint, Depth of Book, Historical Bars

### Market Data - Crypto
- Crypto Snapshot, Candlesticks

### Market Data - Event
- Event Snapshot, Depth, Bars, Tick

### Instruments
- Stock, Crypto, Futures (by code/symbol/products), Event (categories/series/events/instruments)

### Account
- Account List, Balance, Positions

### Order Management
- Preview, Place, Batch Place, Replace, Cancel
- Order History, Open Orders, Order Detail

### Stock Order Types (US)
- MARKET, LIMIT, STOP_LOSS, STOP_LOSS_LIMIT, TRAILING_STOP_LOSS
- MARKET_ON_OPEN, MARKET_ON_CLOSE, LIMIT_ON_OPEN (institutional)
- Combo: NORMAL, MASTER, STOP_PROFIT, STOP_LOSS, OTO, OCO, OTOCO
- Algo: TWAP, VWAP, POV
- Fractional shares via entrust_type=AMOUNT
- Trading sessions: CORE, ALL, NIGHT

### Order Replace Rules (Futures)
- Market orders: only quantity can be modified
- Limit orders: order_type (to MARKET only), time_in_force, quantity, limit_price
- Stop orders: order_type (to MARKET only), time_in_force, quantity, stop_price
- Stop limit orders: order_type (to LIMIT only), time_in_force, quantity, limit_price, stop_price
- Trailing stop orders: only trailing_stop_step can be modified

### Crypto Notes
- Replace (modify) NOT supported for crypto orders
- Supported order types: MARKET (IOC only), LIMIT (DAY/GTC), STOP_LOSS_LIMIT (DAY/GTC)
- Min position $2 when selling

### Rate Limits
- Market data: 600 req/min
- Order place/replace/cancel: 600 req/min
- Order query: 2 req/2s
- Auth: 10 req/30s
