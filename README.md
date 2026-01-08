# Backtest Service

A minimal backtesting framework for **Polymarket** and **Kalshi** prediction markets using the [Dome API](https://domeapi.io).

## Architecture

- **Data Reading**: Use `DomeBacktestClient` with Dome's read-only API for market data, prices, orderbooks, etc.
- **Trading/Orders**: Use `PolymarketBacktestClient` or `KalshiBacktestClient` as drop-in replacements for the official `py-clob-client` and `kalshi` SDKs.

**Note**: Dome's `create_order()`, `buy()`, and `sell()` methods are **mock/simulation methods** included for completeness and future compatibility (Dome itself is read-only). For real trading, use the native SDK clients.

## How It Works

Swap your `DomeClient` import with `DomeBacktestClient` — it automatically injects historical timestamps into all API calls, letting you replay market data and simulate trades without placing real orders.

**Minimal effort conversion:** Just swap the import, add dates to the config, and call `run()`!

> 📖 **Full migration guide:** See [docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md) for detailed examples

```python
# Production code
from dome_api_sdk import DomeClient
dome = DomeClient({"api_key": "..."})

# Backtest code - just swap import and add dates!
from backtest_service import DomeBacktestClient
from datetime import datetime

dome = DomeBacktestClient({
    "api_key": "your-api-key",
    "start_time": int(datetime(2024, 10, 24).timestamp()),
    "end_time": int(datetime(2024, 10, 25).timestamp()),
})

# Your strategy works the same - use create_order() for trading
async def my_strategy(dome):
    price = await dome.polymarket.markets.get_market_price({"token_id": "..."})
    if dome.portfolio.cash > 100:
        await dome.polymarket.markets.create_order(
            token_id="...",
            side="YES",
            size="1000000000",
            price="0.50",
            order_type="GTC"
        )

# Run it!
result = await dome.run(my_strategy)
print(f"Return: {result.total_return_pct:.2f}%")
```

## Features

- **Historical Data On-Demand** — Uses Dome API's `at_time` parameter, no local data storage needed
- **Market Discovery** — `get_markets()` filters results to prevent lookahead bias
- **Multi-Platform Data** — Full support for Polymarket and Kalshi via Dome's read-only API
- **Trading Support** — Drop-in replacements for `py-clob-client` and `kalshi` SDKs for actual order creation
- **Mock Trading (Dome)** — Optional `create_order()` methods in Dome client for simulation (Dome itself is read-only)
- **Realistic Order Types** — Market, Limit, FOK, GTC, GTD orders with orderbook matching
- **Portfolio Simulation** — Track positions, cash, and P&L without real trades
- **Drop-in Replacement** — Same API interface as the real SDKs

## Installation

```bash
pip install dome-api-sdk
git clone https://github.com/tweidv/backtest-service.git
cd backtest-service
pip install -e .
```

## Quick Start

### Dome API (Data Reading)

Use `DomeBacktestClient` for reading market data (Dome is read-only):

```python
import asyncio
from decimal import Decimal
from datetime import datetime
from backtest_service import DomeBacktestClient

async def my_strategy(dome):
    """Read data from Dome, trade via native SDKs"""
    # Read market data via Dome (read-only)
    markets = await dome.polymarket.markets.get_markets({
        "status": "open",
        "limit": 10
    })
    
    for market in markets.markets:
        price_data = await dome.polymarket.markets.get_market_price({
            "token_id": market.token_id
        })
        print(f"Market: {market.title}, Price: {price_data.price}")
        
        # Note: Dome is read-only. For actual trading, use native SDK clients
        # (see examples below)

async def main():
    dome = DomeBacktestClient({
        "api_key": "YOUR_DOME_API_KEY",
        "start_time": int(datetime(2024, 10, 24).timestamp()),
        "end_time": int(datetime(2024, 10, 25).timestamp()),
        "step": 3600,
        "initial_cash": 10000,
    })
    
    result = await dome.run(my_strategy)
    print(f"Return: {result.total_return_pct:+.2f}%")

asyncio.run(main())
```

**Note**: Dome's `create_order()`, `buy()`, and `sell()` are mock methods included for simulation/forward compatibility. Dome itself is read-only. For actual trading, use the native SDK clients below.

### Native SDKs (Trading/Order Creation)

**For actual order creation, use the native SDK clients** as drop-in replacements for the official SDKs:

**For Polymarket (`py-clob-client`):**
```python
import asyncio
from datetime import datetime

# Live code
# from py_clob_client import ClobClient
# client = ClobClient(api_key="...")

# Backtest - just swap import!
from backtest_service.native import PolymarketBacktestClient

client = PolymarketBacktestClient({
    "dome_api_key": "YOUR_DOME_API_KEY",
    "start_time": int(datetime(2024, 10, 24).timestamp()),
    "end_time": int(datetime(2024, 10, 25).timestamp()),
    "initial_cash": 10000,
})

# Same code as live py-clob-client!
order = await client.create_order(
    token_id="0x123...",
    side="YES",
    size="1000000000",
    price="0.65",
    order_type="GTC"
)
```

**For Kalshi (`kalshi` SDK):**
```python
# Live code
# from kalshi import KalshiClient
# client = KalshiClient(api_key="...")

# Backtest - just swap import!
from backtest_service.native import KalshiBacktestClient

client = KalshiBacktestClient({
    "dome_api_key": "YOUR_DOME_API_KEY",
    "start_time": int(datetime(2024, 10, 24).timestamp()),
    "end_time": int(datetime(2024, 10, 25).timestamp()),
    "initial_cash": 10000,
})

# Same code as live kalshi SDK!
order = await client.create_order(
    ticker="KXNFLGAME-25AUG16ARIDEN-ARI",
    side="yes",
    action="buy",
    count=100,
    order_type="limit",
    yes_price=75
)
```


## Market Discovery

Discover markets dynamically during backtests **without lookahead bias**:

```python
# At backtest time Oct 20, 2024 (before the election):
response = await dome.polymarket.get_markets({
    "status": "open",
    "min_volume": 100000,
    "limit": 10,
})

for market in response.markets:
    print(market.title)              # "Will Trump win the 2024 election?"
    print(market.historical_status)  # "open" — was open at backtest time
    print(market.was_resolved)       # False — election hadn't happened yet
    print(market.winning_side)       # None — outcome is hidden!
    print(market.side_a.id)          # Token ID for trading
```

**Key behaviors:**
- Markets with `start_time > backtest_time` are excluded (didn't exist yet)
- `historical_status` reflects the status **at backtest time**, not current
- `winning_side` is `None` if the market wasn't resolved at backtest time
- Works for Polymarket and Kalshi with full order type support

## API Reference

### DomeBacktestClient

```python
# Initialize
dome = DomeBacktestClient({
    "api_key": "your-api-key",
    "start_time": 1729800000,  # Unix timestamp
    "end_time": 1729886400,    # Unix timestamp
    "step": 3600,              # Optional: seconds between ticks (default 3600)
    "initial_cash": 10000,     # Optional: starting capital (default 10000)
})

# Run backtest
result = await dome.run(strategy_fn)  # get_prices auto-detected!

# Access portfolio
dome.portfolio.cash        # Available cash
dome.portfolio.positions  # Dict[token_id, quantity]

# Polymarket API - Data Reading (Dome is read-only)
await dome.polymarket.markets.get_markets(params)
await dome.polymarket.markets.get_market_price(params)
await dome.polymarket.markets.get_candlesticks(params)
await dome.polymarket.markets.get_orderbooks(params)
await dome.polymarket.orders.get_orders(params)
await dome.polymarket.wallet.get_wallet(params)
await dome.polymarket.wallet.get_wallet_pnl(params)
await dome.polymarket.activity.get_activity(params)

# Polymarket - Mock Trading (optional, Dome is read-only)
# Note: This is a mock method for simulation/forward compatibility
await dome.polymarket.markets.create_order(...)  # Mock method

# For actual trading, use PolymarketBacktestClient (see native SDK section)

# Kalshi API - Data Reading (Dome is read-only)
await dome.kalshi.markets.get_markets(params)
await dome.kalshi.orderbooks.get_orderbooks(params)
await dome.kalshi.trades.get_trades(params)

# Kalshi - Mock Trading (optional, Dome is read-only)
# Note: This is a mock method for simulation/forward compatibility
await dome.kalshi.markets.create_order(...)  # Mock method

# For actual trading, use KalshiBacktestClient (see native SDK section)
```

### BacktestResult

```python
result.initial_cash      # Decimal
result.final_value       # Decimal
result.total_return_pct  # float (percentage)
result.trades            # List[Trade]
result.equity_curve      # List[(timestamp, value)]
```

## Environment Variables

```bash
# Windows
set DOME_API_KEY=your-api-key

# Linux/Mac
export DOME_API_KEY=your-api-key
```

## Rate Limiting

The service includes built-in rate limiting (1.1s between API calls) to comply with Dome API's free tier limits.

## Alternatives

For bulk historical data or faster backtests:
- [DeltaBase](https://deltabase.tech) — CSV downloads
- [Predexon](https://docs.predexon.com) — OHLCV + order flow API

## License

MIT
