# Backtest Service

A minimal backtesting framework for **Polymarket** and **Kalshi** prediction markets using the [Dome API](https://domeapi.io).

## How It Works

Swap your `DomeClient` import with `DomeBacktestClient` — it automatically injects historical timestamps into all API calls, letting you replay market data and simulate trades without placing real orders.

```python
# Production code
from dome_api_sdk import DomeClient
dome = DomeClient({"api_key": "..."})

# Backtest code (same interface!)
from backtest_service import DomeBacktestClient
dome = DomeBacktestClient(api_key, clock, portfolio)
```

## Features

- **Historical Data On-Demand** — Uses Dome API's `at_time` parameter, no local data storage needed
- **Market Discovery** — `get_markets()` filters results to prevent lookahead bias
- **Multi-Platform** — Supports both Polymarket and Kalshi
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

```python
import asyncio
from decimal import Decimal
from backtest_service import BacktestRunner

TOKEN_ID = "21742633143463906290569050155826241533067272736897614950488156847949938836455"

async def my_strategy(dome, portfolio):
    """Your strategy - same code works in production!"""
    price_data = await dome.polymarket.get_market_price({"token_id": TOKEN_ID})
    price = Decimal(str(price_data.price))
    
    if price < Decimal("0.5") and portfolio.cash > 100:
        dome.polymarket.buy(TOKEN_ID, Decimal(100), price)

async def get_prices(dome):
    """Get current prices for portfolio valuation."""
    data = await dome.polymarket.get_market_price({"token_id": TOKEN_ID})
    return {TOKEN_ID: Decimal(str(data.price))}

async def main():
    runner = BacktestRunner(
        api_key="YOUR_DOME_API_KEY",
        start_time=1729800000,  # Oct 24, 2024
        end_time=1729886400,    # Oct 25, 2024
        step=3600,              # 1 hour intervals
        initial_cash=Decimal("10000"),
    )
    
    result = await runner.run(my_strategy, get_prices)
    
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
- Works for both Polymarket and Kalshi

## API Reference

### BacktestRunner

```python
runner = BacktestRunner(
    api_key="...",           # Dome API key
    start_time=1729800000,   # Unix timestamp
    end_time=1729886400,     # Unix timestamp
    step=3600,               # Seconds between ticks (default: 1 hour)
    initial_cash=10000,      # Starting cash
)

result = await runner.run(strategy_fn, get_prices_fn)
```

### DomeBacktestClient

```python
# Polymarket
await dome.polymarket.get_markets(params)         # Market discovery
await dome.polymarket.get_market_price(params)    # Historical prices
await dome.polymarket.get_market(params)          # Market details
await dome.polymarket.get_orderbook_history(params)
await dome.polymarket.get_trade_history(params)
dome.polymarket.buy(token_id, quantity, price)    # Simulated
dome.polymarket.sell(token_id, quantity, price)   # Simulated

# Kalshi
await dome.kalshi.get_markets(params)             # Market discovery
await dome.kalshi.get_orderbooks(params)
dome.kalshi.buy(ticker, quantity, price)          # Simulated
dome.kalshi.sell(ticker, quantity, price)         # Simulated
```

### BacktestResult

```python
result.initial_cash      # Decimal
result.final_value       # Decimal
result.total_return      # Decimal (final - initial)
result.total_return_pct  # float (percentage)
result.trades            # List[Trade]
result.equity_curve      # List[(timestamp, value)]
```

### Portfolio

```python
portfolio.cash              # Available cash
portfolio.positions         # Dict[token_id, quantity]
portfolio.trades            # List of executed trades
portfolio.get_value(prices) # Total portfolio value
```

### HistoricalMarket

```python
market.market_slug        # Market identifier
market.title              # Market question
market.start_time         # When trading started
market.end_time           # Scheduled resolution
market.close_time         # When trading closed
market.side_a             # First outcome (id, label)
market.side_b             # Second outcome (id, label)
market.historical_status  # "open" or "closed" at backtest time
market.was_resolved       # Whether outcome was known at backtest time
market.winning_side       # Winner (only if was_resolved=True)
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
