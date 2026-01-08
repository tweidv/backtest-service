# Backtest Service

A minimal backtesting framework for **Polymarket** and **Kalshi** prediction markets using the [Dome API](https://domeapi.io).

Supports **three ways to trade**:
1. **Dome API** (read-only) - Use `DomeBacktestClient` with simulated `buy()`/`sell()` methods
2. **Polymarket Native SDK** - Use `PolymarketBacktestClient` as drop-in replacement for `py-clob-client`
3. **Kalshi Native SDK** - Use `KalshiBacktestClient` as drop-in replacement for `kalshi` SDK

All backtest clients support **realistic order types**: Market, Limit, FOK (Fill-or-Kill), GTC (Good-Till-Cancel), and GTD (Good-Till-Date) orders with proper orderbook matching.

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

# Your strategy works the same - just access portfolio via dome.portfolio
async def my_strategy(dome):
    price = await dome.polymarket.get_market_price({"token_id": "..."})
    if dome.portfolio.cash > 100:
        dome.polymarket.buy(...)

# Run it!
result = await dome.run(my_strategy)
print(f"Return: {result.total_return_pct:.2f}%")
```

## Features

- **Historical Data On-Demand** — Uses Dome API's `at_time` parameter, no local data storage needed
- **Market Discovery** — `get_markets()` filters results to prevent lookahead bias
- **Multi-Platform** — Full support for Polymarket and Kalshi via Dome API
- **Native SDK Support** — Drop-in replacements for `py-clob-client` and `kalshi` SDKs
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

### Option 1: Dome API (Recommended for Multi-Platform)

```python
import asyncio
from decimal import Decimal
from datetime import datetime
from backtest_service import DomeBacktestClient

TOKEN_ID = "21742633143463906290569050155826241533067272736897614950488156847949938836455"

async def my_strategy(dome):
    """Your strategy - works in both production and backtest!"""
    price_data = await dome.polymarket.markets.get_market_price({"token_id": TOKEN_ID})
    price = Decimal(str(price_data.price))
    
    # Use create_order() for full control (matches native SDKs)
    if price < Decimal("0.5") and dome.portfolio.cash > 100:
        await dome.polymarket.markets.create_order(
            token_id=TOKEN_ID,
            side="YES",
            size="1000000000",
            price="0.48",
            order_type="GTC"  # Limit order
        )
    
    # Or use convenience methods
    # dome.polymarket.markets.buy(TOKEN_ID, Decimal(100), price)

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
    print(f"Trades: {len(result.trades)}")

asyncio.run(main())
```

### Option 2: Polymarket Native SDK (Drop-in Replacement)

```python
import asyncio
from datetime import datetime
from backtest_service.native import PolymarketBacktestClient

async def my_strategy():
    # Backtest mode - just swap import!
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
    
    print(f"Order Status: {order['status']}")
    print(f"Filled: {order['filled_size']}")

asyncio.run(my_strategy())

# Live mode - just change config!
# client = PolymarketBacktestClient({
#     "mode": "live",
#     "polymarket_api_key": "YOUR_POLYMARKET_API_KEY",
# })
```

### Option 3: Kalshi Native SDK (Drop-in Replacement)

```python
import asyncio
from datetime import datetime
from backtest_service.native import KalshiBacktestClient

async def my_strategy():
    # Backtest mode
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
        yes_price=75  # cents
    )
    
    print(f"Order Status: {order['status']}")
    print(f"Filled: {order['filled_count']}")

asyncio.run(my_strategy())
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

# Polymarket API (fully supported)
await dome.polymarket.markets.get_markets(params)
await dome.polymarket.markets.get_market_price(params)
await dome.polymarket.markets.create_order(
    token_id="0x123...",
    side="YES",
    size="1000000000",
    price="0.65",
    order_type="GTC"  # MARKET, FOK, GTC, or GTD
)
# Convenience methods (use create_order() for full control)
dome.polymarket.markets.buy(token_id, quantity, price)
dome.polymarket.markets.sell(token_id, quantity, price)

# Kalshi API (fully supported)
await dome.kalshi.markets.get_markets(params)
await dome.kalshi.orderbooks.get_orderbooks(params)
await dome.kalshi.markets.create_order(
    ticker="KXNFLGAME-25AUG16ARIDEN-ARI",
    side="yes",
    action="buy",
    count=100,
    order_type="limit",  # limit or market
    yes_price=75  # cents (0-100)
)
# Convenience methods
dome.kalshi.markets.buy(ticker, quantity, price)
dome.kalshi.markets.sell(ticker, quantity, price)
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
