# API Structure Documentation

## Organization

The codebase is organized into two main parts:

1. **Dome API Client** (`backtest_service/api/`) - Main backtest client using Dome's unified API
2. **Native SDK Clients** (`backtest_service/native/`) - Optional drop-in replacements for official SDKs

### Dome API Structure

The API module is organized into platform-specific subdirectories matching Dome's structure:

```
backtest_service/api/
├── __init__.py              # Main exports
├── client.py                # DomeBacktestClient (main client)
├── models.py                # Data models (HistoricalMarket, etc.)
├── base_api.py              # BasePlatformAPI (shared functionality)
├── polymarket/              # Polymarket API namespaces
│   ├── __init__.py
│   ├── namespace.py         # PolymarketNamespace (main)
│   ├── markets.py           # PolymarketMarketsNamespace
│   ├── orders.py            # PolymarketOrdersNamespace
│   ├── wallet.py            # PolymarketWalletNamespace
│   └── activity.py           # PolymarketActivityNamespace
├── kalshi/                  # Kalshi API namespaces
│   ├── __init__.py
│   ├── namespace.py         # KalshiNamespace (main)
│   ├── markets.py           # KalshiMarketsNamespace
│   ├── orderbooks.py        # KalshiOrderbooksNamespace
│   └── trades.py            # KalshiTradesNamespace
├── matching_markets/        # Matching markets namespaces
└── crypto_prices/           # Crypto prices namespaces
```

### Native SDK Clients (Optional)

Separate, optional clients for users who use official SDKs directly:

```
backtest_service/native/
├── __init__.py              # Exports
├── polymarket.py            # PolymarketBacktestClient (drop-in for py-clob-client)
└── kalshi.py                # KalshiBacktestClient (drop-in for kalshi SDK)
```

### Simulation Infrastructure

Order simulation components shared by all clients:

```
backtest_service/simulation/
├── orderbook.py             # OrderbookSimulator (historical orderbook matching)
├── orders.py                # OrderManager, SimulatedOrder (order management)
├── portfolio.py             # Portfolio (cash, positions, trades)
├── clock.py                 # SimulationClock (time control)
└── runner.py                # BacktestRunner
```

## Structure Matches Dome Exactly

### Polymarket
- `dome.polymarket.markets.get_markets()`
- `dome.polymarket.markets.get_market_price()`
- `dome.polymarket.markets.get_candlesticks()`
- `dome.polymarket.markets.get_orderbooks()`
- `dome.polymarket.orders.get_orders()`
- `dome.polymarket.wallet.get_wallet()`
- `dome.polymarket.wallet.get_wallet_pnl()`
- `dome.polymarket.activity.get_activity()`

### Kalshi
- `dome.kalshi.markets.get_markets()`
- `dome.kalshi.orderbooks.get_orderbooks()`
- `dome.kalshi.trades.get_trades()`

## Implementation Details

### Dome API Client
- **Read-only** - Only for data access (markets, prices, orderbooks, etc.)
- Each namespace class inherits from `BasePlatformAPI`
- Implementation functions are inlined in namespace files (no separate impl files)
- All methods include parameter validation matching Dome docs
- Historical filtering applied automatically (caps times at backtest time)
- Rate limiting and retry logic in `BasePlatformAPI._call_api()`
- `create_order()`, `buy()`, `sell()` are **mock/simulation methods** (Dome itself is read-only, these were added for completeness/forward compatibility)

### Native SDK Clients
- `PolymarketBacktestClient` - Drop-in replacement for `py-clob-client.ClobClient` (for actual trading)
- `KalshiBacktestClient` - Drop-in replacement for `kalshi.KalshiClient` (for actual trading)
- Both use Dome API for historical data but match native SDK signatures exactly
- Use these for order creation and trading (Dome is read-only)

## Removed Files

- `platform_api.py` - Old flattened API (replaced by namespace structure)
- `kalshi_api.py` - Old flattened API (replaced by namespace structure)
- `polymarket_namespaces.py` - Consolidated into `polymarket/` subdirectory
- `kalshi_namespaces.py` - Consolidated into `kalshi/` subdirectory
- `platform_api_impl.py` - Implementation functions inlined into namespace files

