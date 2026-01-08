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
- **Transaction Fees** — Realistic fee calculation for Polymarket and Kalshi (enabled by default)
- **Interest Accrual** — Kalshi APY interest on cash and positions (optional)
- **Drop-in Replacement** — Same API interface as the real SDKs

## Known Limitations

### Kalshi Support

⚠️ **Kalshi support has been improved but still has some limitations due to Dome API constraints:**

1. **Portfolio Valuation**: ✅ **Fixed** - Kalshi positions are now automatically valued using orderbook data. The system tracks YES and NO positions separately using composite keys (`ticker:YES` or `ticker:NO`). If automatic price detection fails, you can provide a custom `get_prices` function to `dome.run()`.

2. **Position Side Tracking**: ✅ **Fixed** - Kalshi positions now track YES vs NO side separately. Positions are stored as `ticker:YES` or `ticker:NO` to prevent netting.

3. **Matching Markets**: ✅ **Fixed** - Historical filtering is now implemented. Markets are filtered based on `start_time` if available. Markets without `start_time` are included (better safe than sorry to avoid false negatives).

**Note**: Dome API's Kalshi support is more limited than Polymarket support. For full Kalshi backtesting, consider using the native `KalshiBacktestClient` which has better support.

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
    "enable_fees": True,       # Optional: enable transaction fees (default: True)
    "enable_interest": False,  # Optional: enable Kalshi interest accrual (default: False)
    "interest_apy": 0.04,      # Optional: Kalshi APY rate (default: 0.04 = 4%)
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
result.initial_cash              # Decimal
result.final_value               # Decimal
result.total_return_pct          # float (percentage)
result.trades                    # List[Trade] - each Trade has a 'fee' field
result.equity_curve              # List[(timestamp, value)]
result.total_fees_paid           # Decimal - total fees paid
result.total_interest_earned     # Decimal - total interest earned (Kalshi)

# Net returns after fees
result.net_return_after_fees     # Decimal - return after fees (includes interest)
result.net_return_after_fees_pct # float - percentage after fees

# Access fee information from portfolio
portfolio.total_fees_paid  # Total fees paid during backtest
if portfolio.interest_accrual:
    portfolio.interest_accrual.total_interest_paid  # Total interest earned (Kalshi)
```

## Transaction Fees

Transaction fees are **enabled by default** to provide realistic backtest results. Fees are automatically calculated and applied based on the platform and order type.

### Maker vs Taker Orders

Fees depend on whether your order is a **maker** (provides liquidity) or **taker** (takes liquidity):

- **Market orders**: Always takers (take liquidity immediately)
- **Limit orders that fill immediately**: Takers (cross the spread)
- **Limit orders that rest on book**: Makers (provide liquidity when filled later)

The system automatically detects this based on order execution:
- If a limit order fills immediately → taker fee
- If a limit order goes to pending and fills later → maker fee/rebate

### Polymarket Fees
- **Global Platform**: No fees (makers and takers)
- **US Market (QCEX)**: 0.01% taker fee (makers: no fee)
- **15-minute Crypto Markets**: Taker fees with maker rebates

### Kalshi Fees
Kalshi uses a dynamic fee structure based on contract price and probability:

**Formula**: `fees = round_up(0.07 × C × P × (1 - P))`
- `C` = number of contracts
- `P` = contract price in dollars (0.5 for 50 cents)

**Examples**:
- 100 contracts @ $0.50: fee ≈ $1.75
- Higher fees for extreme probabilities (near $0.01 or $0.99)
- Lower fees for 50/50 contracts (near $0.50)

**Disable fees** (for comparison):
```python
dome = DomeBacktestClient({
    "api_key": "...",
    "start_time": ...,
    "end_time": ...,
    "enable_fees": False,  # Disable fees
})
```

## Kalshi Interest (APY)

Kalshi offers interest on cash balances and open positions. Interest accrues daily and is paid monthly.

**Current Rate**: 4.00% APY (variable, subject to change)

**Eligibility**:
- Minimum balance of $250
- Account funded through Kalshi Klear

**Enable interest**:
```python
dome = DomeBacktestClient({
    "api_key": "...",
    "start_time": ...,
    "end_time": ...,
    "enable_interest": True,   # Enable interest accrual
    "interest_apy": 0.04,      # 4% APY (default)
})
```

Interest accrues daily on:
- Cash balances
- End-of-day value of open positions (net portfolio value)

Access interest information:
```python
# After running backtest
portfolio = dome.portfolio
if portfolio.interest_accrual:
    print(f"Total interest earned: ${portfolio.interest_accrual.total_interest_paid:.2f}")
    print(f"Accrued interest: ${portfolio.interest_accrual.accrued_interest:.2f}")
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

## Fee and Interest Summary

**Transaction Fees** (enabled by default):
- **Polymarket Global**: Free
- **Polymarket US**: 0.01% taker fee
- **Kalshi**: Dynamic fees based on contract price (formula: `0.07 × C × P × (1 - P)`)

**Kalshi Interest** (optional, disabled by default):
- **Rate**: 4.00% APY (variable)
- **Accrues**: Daily on cash + positions value
- **Paid**: Monthly (simulated as daily accrual in backtests)
- **Minimum**: $250 balance required

**Example with fees and interest**:
```python
result = await dome.run(my_strategy)
print(f"Gross return: {result.total_return_pct:.2f}%")
print(f"Fees paid: ${result.total_fees_paid:.2f}")
print(f"Interest earned: ${result.total_interest_earned:.2f}")
print(f"Net return: {result.net_return_after_fees_pct:.2f}%")
```

## Alternatives

For bulk historical data or faster backtests:
- [DeltaBase](https://deltabase.tech) — CSV downloads
- [Predexon](https://docs.predexon.com) — OHLCV + order flow API

## License

MIT
