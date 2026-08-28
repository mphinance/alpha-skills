# Webull OpenAPI Reference

## SDK

- Package: `webull-openapi-python-sdk`
- Install: `pip3 install --upgrade webull-openapi-python-sdk`
- Repo: https://github.com/webull-inc/webull-openapi-python-sdk

## Environments & Endpoints

### US Region

| Type | Production | UAT |
|------|-----------|----------|
| HTTP API | `api.webull.com` | `api.sandbox.webull.com` |
| Trading Events (gRPC) | `events-api.webull.com` | `events-api.sandbox.webull.com` |
| Market Data (MQTT) | `data-api.webull.com` | `api.sandbox.webull.com` |

### HK Region

| Type | Production | UAT |
|------|-----------|---------|
| HTTP API | `api.webull.hk` | `api.sandbox.webull.hk` |
| Trading Events (gRPC) | `events-api.webull.hk` | `events-api.sandbox.webull.hk` |
| Market Data (MQTT) | `data-api.webull.hk` | `data-api.sandbox.webull.hk` |

### JP Region

| Type | Production | UAT |
|------|-----------|----------|
| HTTP API | `api.webull.co.jp` | `jp-openapi-alb.uat.webullbroker.com` |
| Trading Events (gRPC) | `events-api.webull.co.jp` | `jp-openapi-events.uat.webullbroker.com` |
| Market Data (MQTT) | `data-api.webull.co.jp` | `data-api.uat.webullbroker.com` |

### SG Region

| Type | Production | UAT |
|------|-----------|----------|
| HTTP API | `api.webull.com.sg` | `sg-api.uat.webullbroker.com` |
| Trading Events (gRPC) | `events-api.webull.com.sg` | `sg-events-api.uat.webullbroker.com` |
| Market Data (MQTT) | `data-api.webull.com.sg` | `data-api.uat.webullbroker.com` |

### TH Region

| Type | Production | UAT |
|------|-----------|----------|
| HTTP API | `api.webull.co.th` | `th-api.uat.webullbroker.com` |
| Trading Events (gRPC) | `events-api.webull.co.th` | `th-events-api.uat.webullbroker.com` |
| Market Data (MQTT) | `data-api.webull.co.th` | `th-api.uat.webullbroker.com` |

### MY Region

| Type | Production | UAT |
|------|-----------|----------|
| HTTP API | `api.webull.com.my` | `my-api.uat.webullbroker.com` |
| Trading Events (gRPC) | `events-api.webull.com.my` | `my-events-api.uat.webullbroker.com` |
| Market Data (MQTT) | `data-api.webull.com.my` | `my-api.uat.webullbroker.com` |

### UK Region

| Type | Production | UAT |
|------|-----------|----------|
| HTTP API | `api.webull-uk.com` | `uk-api.uat.webullbroker.com` |
| Trading Events (gRPC) | `events-api.webull-uk.com` | `uk-events-api.uat.webullbroker.com` |
| Market Data (MQTT) | `data-api.webull-uk.com` | `uk-api.uat.webullbroker.com` |

### MX Region

| Type | Production | UAT |
|------|-----------|----------|
| HTTP API | `api.webull.com.mx` | `us-openapi-alb.uat.webullbroker.com` |
| Trading Events (gRPC) | `events-api.webull.com.mx` | `us-openapi-events.uat.webullbroker.com` |
| Market Data (MQTT) | `data-api.webull.com.mx` | `us-openapi-quotes-api.uat.webullbroker.com` |

### BR Region

| Type | Production | UAT |
|------|-----------|----------|
| HTTP API | `api.webull.com.br` | `us-openapi-alb.uat.webullbroker.com` |
| Trading Events (gRPC) | `events-api.webull.com.br` | `us-openapi-events.uat.webullbroker.com` |
| Market Data (MQTT) | `data-api.webull.com.br` | `us-openapi-quotes-api.uat.webullbroker.com` |

### EU Region

| Type | Production | UAT |
|------|-----------|----------|
| HTTP API | `api.webull.eu` | `eu-api.uat.webullbroker.com` |
| Trading Events (gRPC) | `events-api.webull.eu` | `eu-events-api.uat.webullbroker.com` |
| Market Data (MQTT) | `api.webull.eu` | `eu-api.uat.webullbroker.com` |

### ZA Region

| Type | Production | UAT |
|------|-----------|----------|
| HTTP API | `api.webull.com.au` | `au-api.uat.webullbroker.com` |
| Trading Events (gRPC) | `events-api.webull.com.au` | `au-events-api.uat.webullbroker.com` |
| Market Data (MQTT) | `api.webull.com.au` | `au-api.uat.webullbroker.com` |

### AU Region

| Type | Production | UAT |
|------|-----------|----------|
| HTTP API | `api.webull.com.au` | `au-api.uat.webullbroker.com` |
| Trading Events (gRPC) | `events-api.webull.com.au` | `au-events-api.uat.webullbroker.com` |
| Market Data (MQTT) | `api.webull.com.au` | `au-api.uat.webullbroker.com` |

## Feature Matrix by Region

| Feature | US | HK | JP | SG | TH | MY | UK | MX | BR | EU | ZA | AU |
|---------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|:--:|
| Stock trading | Yes | Yes (US/HK/CN) | Yes (US/JP) | Yes (US) | Yes (US) | Yes (US) | Yes (US) | Yes (US) | Yes (US) | Yes (US) | Yes (US) | Yes (US) |
| Options trading | Yes | Yes (US only) | No | No | No | No | No | No | No | No | No | No |
| Futures trading | Yes | Yes | No | No | No | No | No | No | No | No | No | No |
| Crypto trading | Yes | No | No | No | No | No | No | No | No | No | No | No |
| Event contracts | Yes | No | No | No | No | No | No | No | No | No | No | No |
| Combo orders (OTO/OCO/OTOCO) | Yes | No | No | No | No | No | No | No | No | No | No | No |
| Algo orders (TWAP/VWAP/POV) | Yes | No | No | No | No | No | No | No | No | No | No | No |
| Trailing stop loss | Yes | No | No | No | No | No | No | No | No | No | No | No |
| Fractional shares | Yes (US market) | No | No | No | No | No | No | No | No | No | No | No |

## Order Types by Market

### US Market
- `MARKET`, `LIMIT`, `STOP_LOSS`, `STOP_LOSS_LIMIT`, `TRAILING_STOP_LOSS`
- `MARKET_ON_OPEN`, `MARKET_ON_CLOSE`, `LIMIT_ON_OPEN` (institutional)

### HK Market
- `ENHANCED_LIMIT`, `AT_AUCTION`, `AT_AUCTION_LIMIT`
- BCAN (`no_party_ids`) required for institutional clients only; retail clients do not need it
- Board lot sizes vary by stock

### CN Market (A-Share via Stock Connect, HK region only)
- `LIMIT` only
- Disabled by default — contact Webull support to enable

### JP Market
- `LIMIT`, `MARKET`
- US market orders via JP: `LIMIT`, `MARKET`, `STOP_LOSS`, `STOP_LOSS_LIMIT`
- JP-specific fields: `account_tax_type` (`GENERAL`/`SPECIFIC`), `margin_type`, `position_intent`, `close_contracts`

## Time in Force

| Value | US | HK | JP | SG/TH/MY/UK/MX/BR/EU/ZA/AU |
|-------|:--:|:--:|:--:|:--:|
| `DAY` | Yes | Yes | Yes (JP & US markets) | Yes |
| `GTC` | Yes | Yes | Yes (US market only) | Yes |
| `GTD` | Yes | No | No | No |
| `IOC` | Yes | No | No | No |

## Trading Sessions

| Value | Description | Regions |
|-------|-------------|---------|
| `CORE` | Regular hours (9:30 AM - 4:00 PM ET) | All |
| `ALL` | Extended hours (pre-market + after-hours) | All |
| `NIGHT` | Night session only | All |
| `ALL_DAY` | Included overnight hours, 8:00 p.m. ET - 8:00 p.m. ET the next day | All except US |

## Rate Limits

### US Region
- Auth create/check: 10 req/30s
- Market data: 600 req/min
- Order place/replace/cancel: 600 req/min
- Order query: 2 req/2s

### HK Region
- Market data: 60 req/60s
- Order place: 15 req/s (US), 1 req/s (HK/A-share)
- Order preview: 40 req/10s
- Order query: 40 req/2s

### JP Region
- Instrument lookup: 60 req/min per AppId

### SG / TH / MY / UK / MX / BR Region
- Market data: 300 req/60s
- Order place/replace/cancel: 600 req/60s
- Order query: 2 req/2s
- Auth: 10 req/30s

### EU / ZA / AU Region
- Market data: 60 req/60s
- Order place/replace/cancel: 60 req/60s
- Order query: 2 req/2s
- Auth: 10 req/30s

## Official Documentation

- US: https://developer.webull.com/apis/docs/webull-open-api-reference
- HK: https://developer.webull.hk/apis/docs/webull-open-api-reference
- JP: https://developer.webull.co.jp/apis/docs/webull-open-api-reference
- SG: https://developer.webull.com.sg/apis/docs/
- TH: https://developer.webull.co.th/apis/docs/
- MY: https://developer.webull.com.my/apis/docs/
- UK: https://developer.webull-uk.com/apis/docs/
- MX: https://developer.webull.com.mx/apis/docs/
- BR: https://developer.webull.com.br/apis/docs/
- EU: https://developer.webull.eu/apis/docs/
- ZA: https://developer.webull.co.za/apis/docs/
- AU: https://developer.webull.com.au/apis/docs/
- US LLM: https://developer.webull.com/apis/llms.txt
- HK LLM: https://developer.webull.hk/apis/llms.txt
- JP LLM: https://developer.webull.co.jp/apis/llms.txt
- SG LLM: https://developer.webull.com.sg/apis/llms.txt
- TH LLM: https://developer.webull.co.th/apis/llms.txt
- MY LLM: https://developer.webull.com.my/apis/llms.txt
- UK LLM: https://developer.webull-uk.com/apis/llms.txt
- MX LLM: https://developer.webull.com.mx/apis/llms.txt
- BR LLM: https://developer.webull.com.br/apis/llms.txt
- EU LLM: https://developer.webull.eu/apis/llms.txt
- ZA LLM: https://developer.webull.co.za/apis/llms.txt
- AU LLM: https://developer.webull.com.au/apis/llms.txt
