# Backtest Service

A minimal backtesting framework for **Polymarket** and **Kalshi** prediction markets using the [Dome API](https://domeapi.io).

**Note:** Kalshi support is partially implemented. Market discovery and orderbooks work. Simulated trading (`buy()`/`sell()`) works for backtesting. These methods are included for forward compatibility - if Dome adds Kalshi trading support in the future, your backtest code will work seamlessly. Currently, for live Kalshi trading, you'd need to use Kalshi's API directly. Auto price detection for portfolio valuation is not yet available - you'll need to provide a `get_prices` function when using Kalshi positions. Polymarket is fully supported with auto price detection and matches the live API interface.

## How It Works

Swap your `DomeClient` import with `DomeBacktestClient` — it automatically injects historical timestamps into all API calls, letting you replay market data and simulate trades without placing real orders.

**Minimal effort conversion:** Just swap the import, add dates to the config, and call `run()`!

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
- **Multi-Platform** — Full support for Polymarket; Kalshi trading works but requires manual `get_prices` function for portfolio valuation (see note above)
- **Portfolio Simulation** — Track positions, cash, and P&L without real trades
- **Drop-in Replacement** — Same API interface as the real Dome SDK

## Installation

```bash
pip install dome-api-sdk
git clone https://github.com/tweidv/backtest-service.git
cd backtest-service
pip install -e .
```

## Quick Start

**New simplified interface (recommended):**

```python
import asyncio
from decimal import Decimal
from datetime import datetime
from backtest_service import DomeBacktestClient

TOKEN_ID = "21742633143463906290569050155826241533067272736897614950488156847949938836455"

async def my_strategy(dome):
    """Your strategy - works in both production and backtest!"""
    price_data = await dome.polymarket.get_market_price({"token_id": TOKEN_ID})
    price = Decimal(str(price_data.price))
    
    # Access portfolio via dome.portfolio
    if price < Decimal("0.5") and dome.portfolio.cash > 100:
        dome.polymarket.buy(TOKEN_ID, Decimal(100), price)

async def main():
    # Just swap import and add dates - that's it!
    dome = DomeBacktestClient({
        "api_key": "YOUR_DOME_API_KEY",
        "start_time": int(datetime(2024, 10, 24).timestamp()),
        "end_time": int(datetime(2024, 10, 25).timestamp()),
        "step": 3600,  # 1 hour intervals (optional)
        "initial_cash": 10000,  # Starting capital (optional)
    })
    
    # No get_prices function needed - auto-detects!
    result = await dome.run(my_strategy)
    
    print(f"Return: {result.total_return_pct:+.2f}%")
    print(f"Trades: {len(result.trades)}")

asyncio.run(main())
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
- Works for Polymarket (fully supported) and Kalshi (market discovery and trading work, but auto price detection for portfolio valuation requires manual `get_prices` function)

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
await dome.polymarket.get_markets(params)
await dome.polymarket.get_market_price(params)
dome.polymarket.buy(token_id, quantity, price)
dome.polymarket.sell(token_id, quantity, price)

# Kalshi API (data access works, simulated trading for backtesting)
await dome.kalshi.get_markets(params)         # ✅ Works (matches live API)
await dome.kalshi.get_orderbooks(params)     # ✅ Works (matches live API)
dome.kalshi.buy(ticker, quantity, price)      # ✅ Backtest works (forward-compatible if Dome adds support)
dome.kalshi.sell(ticker, quantity, price)     # ✅ Backtest works (forward-compatible if Dome adds support)
# Note: Currently, for live Kalshi trading, use Kalshi's API directly (not through Dome)
# Note: These methods are included for forward compatibility - if Dome adds Kalshi trading, your code will work
# Note: For portfolio valuation, provide get_prices function when calling dome.run()
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
