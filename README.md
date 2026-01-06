# Backtest Service

Minimal backtesting for Kalshi/Polymarket via Dome API.

**Core idea**: Swap your `DomeClient` import with `DomeBacktestClient` — it injects `at_time` into all API calls to replay historical data.

## Install

```bash
pip install dome-api-sdk
```

## Quick Start

```python
import asyncio
from decimal import Decimal
from backtest_service import DomeBacktestClient, BacktestRunner

# 1. Define your strategy (same code as production!)
async def my_strategy(dome: DomeBacktestClient, portfolio):
    token_id = "your-token-id"
    
    # Get historical price at current simulation time
    price_data = await dome.polymarket.get_market_price({"token_id": token_id})
    price = Decimal(str(price_data.price))
    
    # Buy if cheap
    if price < Decimal("0.5") and portfolio.cash > 100:
        dome.polymarket.buy(token_id, quantity=Decimal(10), price=price)
    
    # Sell if expensive
    elif price > Decimal("0.7") and token_id in portfolio.positions:
        dome.polymarket.sell(token_id, quantity=portfolio.positions[token_id], price=price)


# 2. Define how to get prices for portfolio valuation
async def get_prices(dome):
    token_id = "your-token-id"
    price_data = await dome.polymarket.get_market_price({"token_id": token_id})
    return {token_id: Decimal(str(price_data.price))}


# 3. Run backtest
async def main():
    runner = BacktestRunner(
        api_key="YOUR_DOME_API_KEY",  # or use os.environ["DOME_API_KEY"]
        start_time=1704067200,        # Jan 1, 2024 (unix timestamp)
        end_time=1704672000,          # Jan 8, 2024
        step=3600,                    # 1 hour intervals
        initial_cash=Decimal(10000),
    )
    
    result = await runner.run(my_strategy, get_prices)
    
    print(f"Initial: ${result.initial_cash}")
    print(f"Final:   ${result.final_value}")
    print(f"Return:  {result.total_return_pct:.2f}%")
    print(f"Trades:  {len(result.trades)}")

asyncio.run(main())
```

## API Reference

### DomeBacktestClient

Drop-in replacement for `DomeClient`. Supports both platforms:

```python
# Polymarket
await dome.polymarket.get_market_price({"token_id": "..."})
await dome.polymarket.get_market({"token_id": "..."})
await dome.polymarket.get_markets({"status": "open", "limit": 10})  # Market discovery!
await dome.polymarket.get_orderbook_history({"token_id": "..."})
await dome.polymarket.get_trade_history({"token_id": "..."})
dome.polymarket.buy(token_id, quantity, price)
dome.polymarket.sell(token_id, quantity, price)

# Kalshi
await dome.kalshi.get_markets({"status": "open", "limit": 10})
dome.kalshi.buy(ticker, quantity, price)
dome.kalshi.sell(ticker, quantity, price)
```

### Market Discovery (Historical)

The `get_markets()` method filters results to prevent **lookahead bias**:

```python
# At backtest time Oct 15, 2024 (before election):
response = await dome.polymarket.get_markets({"status": "open", "min_volume": 1000000})

for market in response.markets:
    print(market.title)
    print(market.historical_status)  # "open" or "closed" at backtest time
    print(market.was_resolved)       # False - election hadn't happened yet
    print(market.winning_side)       # None - outcome hidden!
```

**Key behaviors:**
- Markets with `start_time > backtest_time` are excluded (didn't exist yet)
- `historical_status` reflects status AT backtest time, not current status
- `winning_side` is `None` if market wasn't resolved at backtest time
- `was_resolved` tells you if outcome was known at backtest time

This lets you build strategies that discover markets dynamically without knowing the future!

### BacktestRunner

```python
runner = BacktestRunner(
    api_key="...",
    start_time=1704067200,  # Unix timestamp
    end_time=1704672000,
    step=3600,              # Seconds between ticks (default: 1 hour)
    initial_cash=10000,
)

result = await runner.run(strategy_fn, get_prices_fn)
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

Available in your strategy function:

```python
portfolio.cash                    # Decimal - available cash
portfolio.positions               # Dict[token_id, Decimal] - quantities held
portfolio.trades                  # List[Trade] - executed trades
portfolio.get_value(prices)       # Total value given current prices
```

## Environment Variable

Set your API key as an environment variable:

```bash
# Windows
set DOME_API_KEY=your-api-key

# Linux/Mac
export DOME_API_KEY=your-api-key
```

Then in code:

```python
import os
runner = BacktestRunner(api_key=os.environ["DOME_API_KEY"], ...)
```

## How It Works

1. `BacktestRunner` creates a `SimulationClock` starting at `start_time`
2. Each tick: clock advances by `step` seconds, your strategy runs
3. All Dome API calls automatically get `at_time=clock.current_time` injected
4. `buy()`/`sell()` calls update the `Portfolio` (no real orders placed)
5. At end, returns `BacktestResult` with P&L and trade history

## Data Sources

This service uses **Dome API** for historical data (on-demand, no storage needed).

Alternatives for bulk/faster data:
- [DeltaBase](https://deltabase.tech) - CSV downloads
- [Predexon](https://docs.predexon.com) - OHLCV + order flow API

