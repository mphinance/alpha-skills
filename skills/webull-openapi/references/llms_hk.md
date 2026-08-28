# Source: https://developer.webull.hk/apis/llms.txt
# Fetched: 2026-04-07

## Base URLs

### Production
- HTTP API: api.webull.hk
- Trading Events (gRPC): events-api.webull.hk
- Market Data Streaming (MQTT): data-api.webull.hk

### Sandbox
- HTTP API: api.sandbox.webull.hk
- Trading Events (gRPC): events-api.sandbox.webull.hk
- Market Data Streaming (MQTT): data-api.sandbox.webull.hk

## Key Differences from US

### Markets Supported
- US stocks, HK stocks, CN A-shares (via Stock Connect)

### Order Types by Market
- US: LIMIT, MARKET, STOP_LOSS, STOP_LOSS_LIMIT, MARKET_ON_OPEN, MARKET_ON_CLOSE
- HK: ENHANCED_LIMIT, AT_AUCTION, AT_AUCTION_LIMIT
- CN (A-Share): LIMIT only

### HK-Specific
- BCAN required (no_party_ids parameter) for institutional clients only
- Board lot sizes vary by stock
- No combo orders, no algo orders
- No futures, crypto, or event contracts
- Trading sessions: CORE, ALL_DAY, NIGHT, ALL

### Rate Limits (HK)
- Market data: 60 req/60s (vs US 600 req/min)
- Order place: 15 req/s (US), 1 req/s (HK/A-share)
- Order preview: 40 req/10s
- Order query: 40 req/2s

### Additional HK Features
- Display Solution API (co-branding)
- Broker API (omnibus/virtual accounts)
- News, Corporate Actions, Screener APIs
