# Webull OpenAPI Documentation

## Guides

### Getting Started
- [Welcome to Webull OpenAPI](https://developer.webull.co.th/apis/docs.md): Platform overview covering Trading API and Market Data API for programmatic access to the US market.
- [About Webull OpenAPI](https://developer.webull.co.th/apis/docs/about-open-api.md): OpenAPI platform capabilities, supported protocols (HTTP, MQTT, gRPC), supported markets, and official SDK overview.
- [Getting Started](https://developer.webull.co.th/apis/docs/getting-started.md): Step-by-step guide from API access request to first API call, covering SDK installation, credentials setup, and API exploration.
- [SDKs and Tools](https://developer.webull.co.th/apis/docs/sdk.md): SDK installation for Python and Java, API environments (production and test), shared test accounts, and management tools.
- [Additional Resources](https://developer.webull.co.th/apis/docs/resources.md): Learning materials, SDK source code, support channels, and legal disclosures.

### Authentication
- [Authentication Overview](https://developer.webull.co.th/apis/docs/authentication/overview.md): Dual-layer security using HMAC-SHA256 signature and Token-based 2FA, required request headers, and credential management.
- [Individual Application Process](https://developer.webull.co.th/apis/docs/authentication/individual-application.md): Step-by-step guide for individual traders to apply for API access, register an application, and generate App Key and App Secret.
- [Signature](https://developer.webull.co.th/apis/docs/authentication/signature.md): HMAC-SHA256 signature generation algorithm, request composition rules, and a complete worked example.
- [Token](https://developer.webull.co.th/apis/docs/authentication/token.md): Token lifecycle management including creation, 2FA verification via Webull App, status checks, storage, and usage in API requests.

### Market Data API
- [Market Data API Overview](https://developer.webull.co.th/apis/docs/market-data-api/overview.md): Supported markets and products, available HTTP and streaming endpoints, rate limits, and market data permission requirements.
- [Market Data API Getting Started](https://developer.webull.co.th/apis/docs/market-data-api/getting-started.md): Quick start guide covering SDK installation, fetching historical bars, and subscribing to real-time quotes via MQTT.
- [Data API](https://developer.webull.co.th/apis/docs/market-data-api/data-api.md): HTTP-based on-demand market data queries including request format, response format, asset categories, and rate limits.
- [Data Streaming API](https://developer.webull.co.th/apis/docs/market-data-api/data-streaming-api.md): Real-time market data streaming via MQTT protocol — connection setup, subscription management, Protobuf message definitions, and error codes.
- [Subscribe Advanced Quotes](https://developer.webull.co.th/apis/docs/market-data-api/subscribe-quotes.md): Step-by-step guide to purchase and activate OpenAPI-specific advanced market data subscriptions.
- [Market Data API FAQ](https://developer.webull.co.th/apis/docs/market-data-api/faq.md): Frequently asked questions about market data access, permissions, rate limits, MQTT connections, and Protobuf parsing.

### Trading API
- [Trading API Overview](https://developer.webull.co.th/apis/docs/trade-api/overview.md): Supported products, feature matrix by order type, full API reference with rate limits, and real-time event subscription.
- [Trading API Getting Started](https://developer.webull.co.th/apis/docs/trade-api/getting-started.md): End-to-end guide covering account retrieval, placing, modifying, and cancelling a stock order, and subscribing to real-time order status updates.
- [Accounts](https://developer.webull.co.th/apis/docs/trade-api/account.md): Account list, balance, and position queries with code examples in Python and Java.
- [Stock Trading](https://developer.webull.co.th/apis/docs/trade-api/stock.md): Full order lifecycle (preview, place, replace, cancel), key parameters, supported order types, time-in-force options, and request examples.
- [Trading API FAQ](https://developer.webull.co.th/apis/docs/trade-api/faq.md): Common questions and troubleshooting for authentication errors, order rejections, client_order_id usage, and real-time event subscriptions.

### General
- [Webull OpenAPI FAQ](https://developer.webull.co.th/apis/docs/faq.md): General frequently asked questions about API application, supported languages, token verification, fees, and support channels.

### AI-Friendly Resources
- [llms.txt](https://developer.webull.co.th/apis/docs/ai-friendly-resources/llm.md): Machine-readable documentation index following the llms.txt standard, Markdown access for all pages, and integration guides for Claude, Cursor, Kiro, ChatGPT, and Gemini.

## API Reference

### Authentication & Token Management
- [Create Token](https://developer.webull.co.th/apis/docs/reference/trade-api/create-token.md): Generate a new authentication token to initiate the 2FA verification flow.
- [Check Token](https://developer.webull.co.th/apis/docs/reference/trade-api/check-token.md): Verify the current status of a token (PENDING, NORMAL, INVALID, EXPIRED).

### Market Data - Stock
- [Tick](https://developer.webull.co.th/apis/docs/reference/trade-api/tick.md): Tick-by-tick transaction records for a specified time range.
- [Snapshot](https://developer.webull.co.th/apis/docs/reference/trade-api/snapshot.md): Real-time market snapshot with latest price, change, and volume.
- [Quotes](https://developer.webull.co.th/apis/docs/reference/trade-api/quotes.md): Order book data at specified depth (price, quantity, orders).
- [Footprint](https://developer.webull.co.th/apis/docs/reference/trade-api/footprint.md): Order flow and volume profile analysis data.
- [Historical Bars](https://developer.webull.co.th/apis/docs/reference/trade-api/historical-bars.md): Batch OHLCV candlestick data for multiple symbols.
- [Historical Bars (Single Symbol)](https://developer.webull.co.th/apis/docs/reference/trade-api/bars.md): OHLCV candlestick data at various granularities for a single symbol.

### Market Data - Streaming
- [Subscribe](https://developer.webull.co.th/apis/docs/reference/trade-api/subscribe.md): Subscribe to real-time market data push via MQTT for specified symbols.
- [Unsubscribe](https://developer.webull.co.th/apis/docs/reference/trade-api/unsubscribe.md): Unsubscribe from real-time market data push.

### Instruments
- [Get Stock Instrument](https://developer.webull.co.th/apis/docs/reference/trade-api/instrument-list.md): Retrieve instrument details for given stock symbols.

### Account Management
- [Account List](https://developer.webull.co.th/apis/docs/reference/trade-api/account-list.md): Retrieve all accounts under your credentials.
- [Account Balance](https://developer.webull.co.th/apis/docs/reference/trade-api/account-balance.md): Query balance, buying power, and cash details for a specific account.
- [Account Positions](https://developer.webull.co.th/apis/docs/reference/trade-api/account-position.md): Retrieve current holdings and positions for a specific account.

### Order Management
- [Preview Order](https://developer.webull.co.th/apis/docs/reference/trade-api/common-order-preview.md): Estimate costs and fees before placing an order.
- [Place Order](https://developer.webull.co.th/apis/docs/reference/trade-api/common-order-place.md): Submit orders for stocks.
- [Replace Order](https://developer.webull.co.th/apis/docs/reference/trade-api/common-order-replace.md): Modify an existing open order.
- [Cancel Order](https://developer.webull.co.th/apis/docs/reference/trade-api/common-order-cancel.md): Cancel a pending or open order.
- [Order History](https://developer.webull.co.th/apis/docs/reference/trade-api/order-history.md): Query historical order records and execution details.
- [Open Orders](https://developer.webull.co.th/apis/docs/reference/trade-api/order-open.md): Retrieve current open orders.
- [Order Detail](https://developer.webull.co.th/apis/docs/reference/trade-api/order-detail.md): Get detailed information for a specific order.

### Trade Events
- [Subscribe Trade Events](https://developer.webull.co.th/apis/docs/reference/custom/subscribe-trade-events.md): Subscribe to real-time order status updates (filled, cancelled, failed, etc.) via gRPC server streaming.

## Changelog
- [Change Logs](https://developer.webull.co.th/apis/docs/changelog.md): Track updates and changes to the API documentation.

---

## Base URLs

### Production Environment
- Trading API: `api.webull.co.th`
- Market Data API: `api.webull.co.th`
- Trading Events (gRPC): `events-api.webull.co.th`
- Market Data Streaming (MQTT): `data-api.webull.co.th`

### Test Environment
- Trading API: `th-api.uat.webullbroker.com`
- Market Data API: `th-api.uat.webullbroker.com`
- Trading Events (gRPC): `th-events-api.uat.webullbroker.com`
- Market Data Streaming (MQTT): `data-api.uat.webullbroker.com`

## Official SDKs

### Python
```bash
pip3 install --upgrade webull-openapi-python-sdk
```

### Java (Maven)
```xml
<dependency>
    <groupId>com.webull.openapi</groupId>
    <artifactId>webull-openapi-java-sdk</artifactId>
    <version>1.0.3</version>
</dependency>
```