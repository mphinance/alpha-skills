# Webull OpenAPI Documentation (MX)

## Guides

### Getting Started
- [Welcome to Webull API](https://developer.webull.com.mx/apis/docs.md): Platform overview covering trading APIs, market data services, and tools for building trading applications for Mexico-based clients.
- [About Webull OpenAPI](https://developer.webull.com.mx/apis/docs/about-open-api.md): OpenAPI platform capabilities and features overview.
- [Getting Started](https://developer.webull.com.mx/apis/docs/getting-started.md): Step-by-step guide from API access request to first API call.
- [SDKs and Tools](https://developer.webull.com.mx/apis/docs/sdk.md): SDK installation, API environments, endpoints, and test accounts.
- [Additional Resources](https://developer.webull.com.mx/apis/docs/resources.md): SDK source code, support channels, and legal disclosures.

### AI Friendly Resources
- [llms.txt](https://developer.webull.com.mx/apis/docs/ai-friendly-resources/llm.md): Machine-readable documentation for AI-assisted development with LLMs, RAG pipelines, and AI coding tools.

### Authentication
- [Authentication Overview](https://developer.webull.com.mx/apis/docs/authentication/overview.md): Signature and Token-based authentication mechanism with security best practices.
- [Individual Application Process](https://developer.webull.com.mx/apis/docs/authentication/individual-application.md): Step-by-step guide for individual users to apply for API access and generate API keys.
- [Signature](https://developer.webull.com.mx/apis/docs/authentication/signature.md): HMAC-SHA1 signature generation, request composition, and required headers for API authentication.
- [Token](https://developer.webull.com.mx/apis/docs/authentication/token.md): Token lifecycle management including creation, 2FA verification, status checks, storage, and usage in API requests.

### Market Data API
- [Market Data API Overview](https://developer.webull.com.mx/apis/docs/market-data-api/overview.md): HTTP-based historical and real-time data retrieval (tick, snapshot, quotes, bars) for stocks; MQTT streaming via WebSocket/TCP; rate limits and subscription requirements.
- [Market Data API Getting Started](https://developer.webull.com.mx/apis/docs/market-data-api/getting-started.md): Quick start guide for SDK installation, API key setup, and requesting historical or real-time market data with code examples.
- [Data API](https://developer.webull.com.mx/apis/docs/market-data-api/data-api.md): HTTP-based market data access covering supported markets and data types.
- [Data Streaming API](https://developer.webull.com.mx/apis/docs/market-data-api/data-streaming-api.md): Real-time market data streaming via MQTT protocol implementation guide.
- [Subscribe Advanced Quotes](https://developer.webull.com.mx/apis/docs/market-data-api/subscribe-quotes.md): Browser-based guide to purchase and activate advanced real-time market data subscriptions.
- [Market Data API FAQ](https://developer.webull.com.mx/apis/docs/market-data-api/faq.md): Frequently asked questions about market data access and usage.

### Trading API
- [Trading API Overview](https://developer.webull.com.mx/apis/docs/trade-api/overview.md): Core trading functionality and capabilities overview.
- [Trading API Getting Started](https://developer.webull.com.mx/apis/docs/trade-api/getting-started.md): Quick start guide for trading API integration.
- [Trading API - Accounts](https://developer.webull.com.mx/apis/docs/trade-api/account.md): Account management, balance queries, and account information retrieval.
- [Trading API - Stocks](https://developer.webull.com.mx/apis/docs/trade-api/stock.md): Stock order placement, modification, cancellation, and status tracking.
- [Trading API - FAQs](https://developer.webull.com.mx/apis/docs/trade-api/faq.md): Common questions and troubleshooting for trading API.

### General
- [Webull OpenAPI FAQs](https://developer.webull.com.mx/apis/docs/faq.md): General frequently asked questions about Webull OpenAPI platform.

## API Reference

### Authentication & Token Management
- [Create Token](https://developer.webull.com.mx/apis/docs/reference/create-token.md): Generate authentication tokens for API access.
- [Check Token](https://developer.webull.com.mx/apis/docs/reference/check-token.md): Verify token validity and status.

### Market Data - Stock
- [Stock Tick](https://developer.webull.com.mx/apis/docs/reference/tick.md): Real-time tick-by-tick trade data for stocks.
- [Stock Snapshot](https://developer.webull.com.mx/apis/docs/reference/snapshot.md): Current market snapshot with latest prices and statistics.
- [Stock Quotes](https://developer.webull.com.mx/apis/docs/reference/quotes.md): Real-time bid/ask quotes and market depth.
- [Stock Footprint](https://developer.webull.com.mx/apis/docs/reference/footprint.md): Order flow and volume profile analysis data.
- [Stock Historical Bars](https://developer.webull.com.mx/apis/docs/reference/historical-bars.md): Historical OHLCV candlestick data for multiple symbols.
- [Stock Historical Bars (Single Symbol)](https://developer.webull.com.mx/apis/docs/reference/bars.md): Historical OHLCV candlestick data for a single symbol.

### Market Data - Streaming
- [Subscribe](https://developer.webull.com.mx/apis/docs/reference/subscribe.md): Subscribe to real-time market data streams via MQTT.
- [Unsubscribe](https://developer.webull.com.mx/apis/docs/reference/unsubscribe.md): Unsubscribe from real-time market data streams.

### Instruments & Symbols
- [Get Stock Instrument](https://developer.webull.com.mx/apis/docs/reference/instrument-list.md): List of available stock symbols and instrument details.

### Account Management
- [Account List](https://developer.webull.com.mx/apis/docs/reference/account-list.md): Retrieve list of user accounts and account IDs.
- [Account Balance](https://developer.webull.com.mx/apis/docs/reference/account-balance.md): Query account balance, buying power, and cash details.
- [Account Positions](https://developer.webull.com.mx/apis/docs/reference/account-position.md): Retrieve current positions and holdings.

### Order Management - Trading
- [Preview Order](https://developer.webull.com.mx/apis/docs/reference/common-order-preview.md): Preview order details and estimated costs before placement.
- [Place Order](https://developer.webull.com.mx/apis/docs/reference/common-order-place.md): Submit new orders.
- [Replace Order](https://developer.webull.com.mx/apis/docs/reference/common-order-replace.md): Modify existing open orders (price, quantity, etc.).
- [Cancel Order](https://developer.webull.com.mx/apis/docs/reference/common-order-cancel.md): Cancel pending or open orders.

### Order Management - Query
- [Order History](https://developer.webull.com.mx/apis/docs/reference/order-history.md): Query historical order records and execution details.
- [Open Orders](https://developer.webull.com.mx/apis/docs/reference/order-open.md): Retrieve list of current open orders.
- [Order Detail](https://developer.webull.com.mx/apis/docs/reference/order-detail.md): Get detailed information for a specific order.

### Trade Events
- [Subscribe Trade Events](https://developer.webull.com.mx/apis/docs/reference/custom/subscribe-trade-events.md): Subscribe to real-time order status change notifications via gRPC.

## Changelog
- [Documentation Changelog](https://developer.webull.com.mx/apis/docs/changelog.md): Track updates, new features, and changes to the API documentation.

---

## Base URLs

### Production Environment
- Trading API: `api.webull.com.mx`

### Test Environment
- HTTP API: `us-openapi-alb.uat.webullbroker.com`
