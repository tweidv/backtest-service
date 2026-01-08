# API Structure Documentation

## Organization

The API module is organized into platform-specific subdirectories matching Dome's structure:

```
backtest_service/api/
├── __init__.py              # Main exports
├── client.py                # DomeBacktestClient
├── models.py                # Data models (HistoricalMarket, etc.)
├── base_api.py              # BasePlatformAPI (shared functionality)
├── polymarket/              # Polymarket API namespaces
│   ├── __init__.py
│   ├── namespace.py         # PolymarketNamespace (main)
│   ├── markets.py           # PolymarketMarketsNamespace
│   ├── orders.py            # PolymarketOrdersNamespace
│   ├── wallet.py            # PolymarketWalletNamespace
│   └── activity.py           # PolymarketActivityNamespace
└── kalshi/                  # Kalshi API namespaces
    ├── __init__.py
    ├── namespace.py         # KalshiNamespace (main)
    ├── markets.py           # KalshiMarketsNamespace
    ├── orderbooks.py        # KalshiOrderbooksNamespace
    └── trades.py            # KalshiTradesNamespace
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

- Each namespace class inherits from `BasePlatformAPI`
- Implementation functions are inlined in namespace files (no separate impl files)
- All methods include parameter validation matching Dome docs
- Historical filtering applied automatically (caps times at backtest time)
- Rate limiting and retry logic in `BasePlatformAPI._call_api()`

## Removed Files

- `platform_api.py` - Old flattened API (replaced by namespace structure)
- `kalshi_api.py` - Old flattened API (replaced by namespace structure)
- `polymarket_namespaces.py` - Consolidated into `polymarket/` subdirectory
- `kalshi_namespaces.py` - Consolidated into `kalshi/` subdirectory
- `platform_api_impl.py` - Implementation functions inlined into namespace files

