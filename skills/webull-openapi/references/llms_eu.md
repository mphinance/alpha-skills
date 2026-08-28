# Webull OpenAPI Documentation (EU)

## Guides

### Getting Started
- [Welcome to Webull API](https://developer.webull.eu/apis/docs.md): Platform overview covering trading APIs, market data services, and tools for building trading applications for EU-based clients.
- [About Webull OpenAPI](https://developer.webull.eu/apis/docs/about-open-api.md): OpenAPI platform capabilities and features overview.
- [Getting Started](https://developer.webull.eu/apis/docs/getting-started.md): Step-by-step guide from API access request to first API call.
- [SDKs and Tools](https://developer.webull.eu/apis/docs/sdk.md): SDK installation, API environments, endpoints, and test accounts.
- [Additional Resources](https://developer.webull.eu/apis/docs/resources.md): SDK source code, support channels, and legal disclosures.

### AI Friendly Resources
- [llms.txt](https://developer.webull.eu/apis/docs/ai-friendly-resources/llm.md): Machine-readable documentation for AI-assisted development with LLMs, RAG pipelines, and AI coding tools.

### Authentication
- [Authentication Overview](https://developer.webull.eu/apis/docs/authentication/overview.md): Signature and Token-based authentication mechanism with security best practices.
- [Individual Application Process](https://developer.webull.eu/apis/docs/authentication/individual-application.md): Step-by-step guide for individual users to apply for API access and generate API keys.
- [Signature](https://developer.webull.eu/apis/docs/authentication/signature.md): HMAC-SHA256 signature generation, request composition, and required headers for API authentication.
- [Token](https://developer.webull.eu/apis/docs/authentication/token.md): Token lifecycle management including creation, 2FA verification, status checks, storage, and usage in API requests.

### Market Data API
- [Market Data API Overview](https://developer.webull.eu/apis/docs/market-data-api/overview.md): HTTP-based historical and real-time data retrieval for stocks, futures, crypto, and event contracts; MQTT streaming via WebSocket/TCP; rate limits and subscription requirements.
- [Market Data API Getting Started](https://developer.webull.eu/apis/docs/market-data-api/getting-started.md): Quick start guide for SDK installation, API key setup, and requesting historical or real-time market data with code examples.
- [Data API](https://developer.webull.eu/apis/docs/market-data-api/data-api.md): HTTP-based market data access covering supported markets and data types.
- [Data Streaming API](https://developer.webull.eu/apis/docs/market-data-api/data-streaming-api.md): Real-time market data streaming via MQTT protocol implementation guide.
- [Subscribe Advanced Quotes](https://developer.webull.eu/apis/docs/market-data-api/subscribe-quotes.md): Browser-based guide to purchase and activate advanced real-time market data subscriptions.
- [Market Data API FAQ](https://developer.webull.eu/apis/docs/market-data-api/faq.md): Frequently asked questions about market data access and usage.

### Trading API
- [Trading API Overview](https://developer.webull.eu/apis/docs/trade-api/overview.md): Core trading functionality and capabilities overview.
- [Trading API Getting Started](https://developer.webull.eu/apis/docs/trade-api/getting-started.md): Quick start guide for trading API integration.
- [Trading API - Accounts](https://developer.webull.eu/apis/docs/trade-api/account.md): Account management, balance queries, and account information retrieval.
- [Trading API - Stocks](https://developer.webull.eu/apis/docs/trade-api/stock.md): Stock order placement, modification, cancellation, and status tracking.
- [Trading API - Options](https://developer.webull.eu/apis/docs/trade-api/options.md): Options trading including single-leg and multi-leg strategies.
- [Trading API - Futures](https://developer.webull.eu/apis/docs/trade-api/futures.md): Futures order placement, modification, and cancellation.
- [Trading API - Crypto](https://developer.webull.eu/apis/docs/trade-api/crypto.md): Cryptocurrency trading operations.
- [Trading API - Event Contract](https://developer.webull.eu/apis/docs/trade-api/event-contract.md): Event contract trading operations.
- [Trading API - FAQs](https://developer.webull.eu/apis/docs/trade-api/faq.md): Common questions and troubleshooting for trading API.

### Connect API
- [About Connect API](https://developer.webull.eu/apis/docs/connect-api/about-connect-api.md): OAuth-based Connect API for third-party integrations.
- [Connect API Authentication](https://developer.webull.eu/apis/docs/connect-api/authentication.md): OAuth authorization flow and token management for Connect API.

### Broker API
- [Broker API Getting Started](https://developer.webull.eu/apis/docs/broker-api/getting-started.md): Getting started guide for broker-level API integration.

### General
- [Webull OpenAPI FAQs](https://developer.webull.eu/apis/docs/faq.md): General frequently asked questions about Webull OpenAPI platform.

## API Reference

### Authentication & Token Management
- [Create Token](https://developer.webull.eu/apis/docs/reference/create-token.md): Generate authentication tokens for API access.
- [Check Token](https://developer.webull.eu/apis/docs/reference/check-token.md): Verify token validity and status.

### Market Data - Stock
- [Stock Tick](https://developer.webull.eu/apis/docs/reference/tick.md): Real-time tick-by-tick trade data for stocks.
- [Stock Snapshot](https://developer.webull.eu/apis/docs/reference/snapshot.md): Current market snapshot with latest prices and statistics.
- [Stock Quotes](https://developer.webull.eu/apis/docs/reference/quotes.md): Real-time bid/ask quotes and market depth.
- [Stock Footprint](https://developer.webull.eu/apis/docs/reference/footprint.md): Order flow and volume profile analysis data.
- [Stock Historical Bars](https://developer.webull.eu/apis/docs/reference/historical-bars.md): Historical OHLCV candlestick data for multiple symbols.
- [Stock Historical Bars (Single Symbol)](https://developer.webull.eu/apis/docs/reference/bars.md): Historical OHLCV candlestick data for a single symbol.

### Market Data - Futures
- [Futures Tick](https://developer.webull.eu/apis/docs/reference/futures-tick.md): Real-time tick-by-tick trade data for futures.
- [Futures Snapshot](https://developer.webull.eu/apis/docs/reference/futures-snapshot.md): Current futures market snapshot.
- [Futures Footprint](https://developer.webull.eu/apis/docs/reference/futures-footprint.md): Futures order flow analysis.
- [Futures Quotes](https://developer.webull.eu/apis/docs/reference/futures-depth-of-book.md): Futures order book depth.
- [Futures Historical Bars](https://developer.webull.eu/apis/docs/reference/futures-historical-bars.md): Historical OHLCV data for futures.

### Market Data - Crypto
- [Crypto Snapshot](https://developer.webull.eu/apis/docs/reference/crypto-snapshot.md): Current cryptocurrency market snapshot.
- [Crypto Candlesticks](https://developer.webull.eu/apis/docs/reference/crypto-bars.md): Historical candlestick data for crypto.

### Market Data - Event Contract
- [Event Snapshot](https://developer.webull.eu/apis/docs/reference/event-snapshot.md): Event contract market snapshot.
- [Event Depth](https://developer.webull.eu/apis/docs/reference/event-depth.md): Event contract order book depth.
- [Event Bars](https://developer.webull.eu/apis/docs/reference/event-bars.md): Event contract historical bars.
- [Event Tick](https://developer.webull.eu/apis/docs/reference/event-tick.md): Event contract tick data.

### Market Data - Streaming
- [Subscribe](https://developer.webull.eu/apis/docs/reference/subscribe.md): Subscribe to real-time market data streams via MQTT.
- [Unsubscribe](https://developer.webull.eu/apis/docs/reference/unsubscribe.md): Unsubscribe from real-time market data streams.

### Instruments & Symbols
- [Get Stock Instrument](https://developer.webull.eu/apis/docs/reference/instrument-list.md): List of available stock symbols and instrument details.
- [Get Crypto Instrument](https://developer.webull.eu/apis/docs/reference/crypto-instrument-list.md): List of available crypto symbols.
- [Get Instrument Code](https://developer.webull.eu/apis/docs/reference/futures-products.md): Futures instrument product codes.
- [Get Instrument by Code](https://developer.webull.eu/apis/docs/reference/futures-instrument-list-by-code.md): Query futures instruments by product code.
- [Get Instrument by Symbol](https://developer.webull.eu/apis/docs/reference/futures-instrument-list.md): Query futures instruments by symbol.
- [Get Event Contract Categories](https://developer.webull.eu/apis/docs/reference/event-categories-list.md): List event contract categories.
- [Get Event Contract Series](https://developer.webull.eu/apis/docs/reference/event-series-list.md): List event contract series.
- [Get Event Contract Events](https://developer.webull.eu/apis/docs/reference/event-events-list.md): List event contract events.
- [Get Event Contract Instrument](https://developer.webull.eu/apis/docs/reference/event-market-list.md): Get event contract instrument details.

### Account Management
- [Account List](https://developer.webull.eu/apis/docs/reference/account-list.md): Retrieve list of user accounts and account IDs.
- [Account Balance](https://developer.webull.eu/apis/docs/reference/account-balance.md): Query account balance, buying power, and cash details.
- [Account Positions](https://developer.webull.eu/apis/docs/reference/account-position.md): Retrieve current positions and holdings.

### Order Management - Trading
- [Preview Order](https://developer.webull.eu/apis/docs/reference/common-order-preview.md): Preview order details and estimated costs before placement.
- [Place Order](https://developer.webull.eu/apis/docs/reference/common-order-place.md): Submit new orders.
- [Order Batch Place](https://developer.webull.eu/apis/docs/reference/order-batch-place.md): Submit multiple orders in a single batch.
- [Replace Order](https://developer.webull.eu/apis/docs/reference/common-order-replace.md): Modify existing open orders (price, quantity, etc.).
- [Cancel Order](https://developer.webull.eu/apis/docs/reference/common-order-cancel.md): Cancel pending or open orders.

### Order Management - Query
- [Order History](https://developer.webull.eu/apis/docs/reference/order-history.md): Query historical order records and execution details.
- [Open Orders](https://developer.webull.eu/apis/docs/reference/order-open.md): Retrieve list of current open orders.
- [Order Detail](https://developer.webull.eu/apis/docs/reference/order-detail.md): Get detailed information for a specific order.

### Trade Events
- [Subscribe Trade Events](https://developer.webull.eu/apis/docs/reference/custom/subscribe-trade-events.md): Subscribe to real-time order status change notifications via gRPC.
- [Subscribe Position Events](https://developer.webull.eu/apis/docs/reference/custom/subscribe-position-events.md): Subscribe to real-time position change notifications via gRPC.

### Connect API
- [Get Authorization Code](https://developer.webull.eu/apis/docs/reference/connect-api/get-authorization-code.md): OAuth authorization code request for third-party integrations.
- [Create And Refresh Token](https://developer.webull.eu/apis/docs/reference/connect-api/create-and-refresh-token.md): Create or refresh OAuth tokens for Connect API.

## Changelog
- [Documentation Changelog](https://developer.webull.eu/apis/docs/changelog.md): Track updates, new features, and changes to the API documentation.

## Base URLs

### Production Environment

| API | Service | Host |
|-----|---------|------|
| Trading API | HTTP API | `api.webull.eu` |
| Market Data API | HTTP API | `api.webull.eu` |
| Trading Events | gRPC | `events-api.webull.eu` |
| Market Data Streaming | MQTT | `data-api.webull.com` |

### Test Environment

| API | Service | Host |
|-----|---------|------|
| Trading API | HTTP API | `eu-api.uat.webullbroker.com` |
| Market Data API | HTTP API | `eu-api.uat.webullbroker.com` |
| Trading Events | gRPC | `eu-events-api.uat.webullbroker.com` |
| Market Data Streaming | MQTT | `us-data-api.uat.webullbroker.com` |

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