# Backtest Service

A backtesting framework for Polymarket and Kalshi prediction markets built around Dome API. Just swap your import from "from dome_api_sdk import DomeClient" to "from backtest_service import DomeBacktestClient" and set the start and end times to go from a live algorithm to a backtest.

## Quick Start

```python
from backtest_service import DomeBacktestClient
from datetime import datetime

# Initialize backtest client
dome = DomeBacktestClient({
    "api_key": "your-dome-api-key",
    "start_time": int(datetime(2024, 11, 1).timestamp()),
    "end_time": int(datetime(2024, 11, 2).timestamp()),
    "initial_cash": 10000,
    "verbose": True,  # See progress in real-time
})

# Define your strategy
async def my_strategy(dome):
    # Get open markets
    markets = await dome.polymarket.markets.get_markets({
        "status": "open",
        "limit": 10
    })
    
    # Check prices and trade
    for market in markets.markets:
        price_data = await dome.polymarket.markets.get_market_price({
            "token_id": market.side_a.id
        })
        
        if price_data.price < 0.5 and dome.portfolio.cash > 100:
            # Create order (matches Dome API format)
            order = await dome.polymarket.markets.create_order(
                token_id=market.side_a.id,
                side="buy",
                size="100000",
                price=str(price_data.price),
                order_type="FOK"
            )

# Run backtest
result = await dome.run(my_strategy)
print(f"Return: {result.total_return_pct:.2f}%")
print(f"Final Value: ${result.final_value:.2f}")
```

## Requirements

- Python 3.9 or higher
- Dome API key ([get one here](https://domeapi.io))

The `dome-api-sdk` dependency will be installed automatically when you install this package.

## Installation

```bash
git clone https://github.com/tweidv/backtest-service.git
cd backtest-service
pip install -e .
```

### Environment Variables

Create a `.env` file in the project root and add your Dome API key:

```
DOME_API_KEY=your-dome-api-key-here
```

The API key will be automatically loaded from the `DOME_API_KEY` environment variable if not provided in the config. Get your API key from [domeapi.io](https://domeapi.io).

## How It Works

The framework simulates trading in the past by maintaining an internal simulation clock (`at_time`) that tracks the current backtest timestamp. Every API call automatically injects this timestamp, ensuring you only see data that existed at that point in time. The framework:

1. **Time Simulation**: Maintains a simulation clock starting at `start_time` that advances by `step` seconds each tick
2. **Historical Data Injection**: Every API call automatically uses the current simulation time, ensuring you only see markets, prices, and orderbooks that existed at that timestamp
3. **Lookahead Prevention**: Market resolution status (`winning_side`, `was_resolved`) is filtered to `None` if the market wasn't resolved yet, preventing you from using future information
4. **Portfolio Simulation**: Tracks cash, positions, fees, and interest exactly as they would have occurred in real trading

Your strategy code stays the same — just swap `DomeClient` for `DomeBacktestClient` and add time bounds.

### Example: Converting Live Code to Backtest

**Live Code:**
```python
from dome_api_sdk import DomeClient

dome = DomeClient({"api_key": "..."})
markets = await dome.polymarket.markets.get_markets({"status": "open"})
```

**Backtest Code:**
```python
from backtest_service import DomeBacktestClient
from datetime import datetime

dome = DomeBacktestClient({
    "api_key": "...",
    "start_time": int(datetime(2024, 11, 1).timestamp()),
    "end_time": int(datetime(2024, 11, 2).timestamp()),
})
markets = await dome.polymarket.markets.get_markets({"status": "open"})
# Same API! ✅
```

## Configuration

### Basic Configuration

```python
dome = DomeBacktestClient({
    "api_key": "your-api-key",           # Optional if DOME_API_KEY env var is set
    "start_time": 1729800000,            # Required: Unix timestamp
    "end_time": 1729886400,              # Required: Unix timestamp
    "step": 3600,                         # Optional: seconds between ticks (default: 3600, minimum: 1)
    "initial_cash": 10000,                # Optional: starting capital (default: 10000)
    "enable_fees": True,                  # Optional: transaction fees (default: True)
    "enable_interest": False,             # Optional: Kalshi interest (default: False)
    "rate_limit_tier": "free",            # Optional: "free", "dev", or "enterprise" (default: "free")
    "verbose": False,                     # Optional: enable progress output (default: False)
    "log_level": "INFO",                  # Optional: logging detail level (default: "INFO")
})
```

- **What is a tick?** A tick is one execution of your strategy function at a specific timestamp. The simulation clock advances forward by `step` seconds after each tick, and your strategy runs again at the new 

### Verbose Mode and Logging

The `verbose` and `log_level` parameters control how much information is displayed during a backtest:

#### Verbose Mode (`verbose`)

When `verbose=True`, the framework displays:
- **Tick Progress**: Shows the current tick number, timestamp, portfolio cash, total value, and number of positions at the start of each tick
- **API Calls**: Lists all API calls made during the backtest (controlled by `log_level`)

#### Log Level (`log_level`)

The `log_level` parameter controls the detail of API call logging when `verbose=True`:

- **`"DEBUG"`**: Shows all API calls **and** their responses/results. Use this when you want to see exactly what data is being returned.
- **`"INFO"`**: Shows API calls but **not** their responses. Use this for a cleaner output that still shows what your strategy is doing.
- **`"WARNING"`** / **`"ERROR"`**: Suppresses API call logging (reserved for actual warnings/errors).

**Example with `verbose=True` and `log_level="DEBUG"`:**

```python
dome = DomeBacktestClient({
    "api_key": "...",
    "start_time": ...,
    "end_time": ...,
    "verbose": True,      # Enable progress output
    "log_level": "DEBUG", # Show API calls AND responses
})

# Output:
# [Tick 1/56] 2024-11-01 00:00:00 | Cash: $10,000.00 | Value: $10,000.00 | Positions: 0
#   [API] 00:00:00 polymarket.PolymarketMarketsNamespace.get_markets({'status': 'open'})
#     -> 50 markets
#   [API] 00:00:01 polymarket.PolymarketMarketsNamespace.get_market_price({'token_id': '...'})
#     -> price=0.65
```

**Example with `verbose=True` and `log_level="INFO"` (default):**

```python
dome = DomeBacktestClient({
    "verbose": True,
    "log_level": "INFO",  # Or omit since INFO is default
})

# Output:
# [Tick 1/56] 2024-11-01 00:00:00 | Cash: $10,000.00 | Value: $10,000.00 | Positions: 0
#   [API] 00:00:00 polymarket.PolymarketMarketsNamespace.get_markets({'status': 'open'})
#   [API] 00:00:01 polymarket.PolymarketMarketsNamespace.get_market_price({'token_id': '...'})
# (API responses not shown)
```

**Recommendation:** Use `verbose=True` with `log_level="INFO"` for development and debugging. Switch to `log_level="DEBUG"` when you need to inspect API responses in detail. Set `verbose=False` for production runs where you only care about the final results.

## Trading

### Strategy Function Signature

Your strategy function should be an async function that takes one parameter:

```python
async def strategy(dome):
    # Access portfolio via dome.portfolio
    cash = dome.portfolio.cash
    positions = dome.portfolio.positions
    # ... your trading logic
```

**Note:** The framework also supports `async def strategy(dome, portfolio)` for backward compatibility, but using `dome.portfolio` is the recommended approach since it matches the live `DomeClient` API.

### Creating Orders

Create orders using Dome API format to match production:

```python
async def strategy(dome):
    # Get market price
    price_data = await dome.polymarket.markets.get_market_price({
        "token_id": "0x123..."
    })
    
    # Create order (matches Dome API router.placeOrder())
    order = await dome.polymarket.markets.create_order(
        token_id="0x123...",
        side="buy",           # "buy" or "sell"
        size="1000000000",    # Order size as string
        price="0.65",         # Limit price as string (0-1)
        order_type="GTC"      # "FOK", "FAK", "GTC", or "GTD"
    )
    
    # Check order status
    if order["status"] == "matched":
        print(f"Order filled at {order['fill_price']}")
```

**Order Types:**
- `"FOK"` (Fill Or Kill): Must fill completely or reject immediately
- `"FAK"` (Fill And Kill): Fill what you can at limit price, cancel remainder
- `"GTC"` (Good Till Cancel): Stays on book until filled or cancelled
- `"GTD"` (Good Till Date): Expires at specified `expiration_time_seconds`

**Order Status:**
- `"matched"` - Order was filled
- `"pending"` - Order is on the book waiting to fill
- `"rejected"` - Order was rejected (e.g., insufficient liquidity)
- `"cancelled"` - Order was cancelled
- `"expired"` - Order expired (GTD orders)

### Native SDK Compatibility

You can also use the native SDK clients for compatibility with `py-clob-client` (Polymarket) or `kalshi` SDK (Kalshi):

```python
from backtest_service.native import PolymarketBacktestClient, KalshiBacktestClient

# Polymarket - matches py-clob-client API
polymarket = PolymarketBacktestClient({
    "dome_api_key": "...",
    "start_time": ...,
    "end_time": ...,
})
order = await polymarket.create_order(
    token_id="0x123...",
    side="YES",  # py-clob-client format
    size="1000000000",
    price="0.65",
    order_type="GTC"
)

# Kalshi - matches kalshi SDK API
kalshi = KalshiBacktestClient({
    "dome_api_key": "...",
    "start_time": ...,
    "end_time": ...,
})
order = await kalshi.create_order(
    ticker="KXNFLGAME-...",
    side="yes",
    action="buy",
    count=100,
    order_type="limit",
    yes_price=75
)
```

## Market Discovery

Discover markets dynamically during backtests without lookahead bias:

```python
async def strategy(dome):
    # Get markets that existed at backtest time
    response = await dome.polymarket.markets.get_markets({
        "status": "open",
        "min_volume": 100000,
        "limit": 10,
    })
    
    for market in response.markets:
        print(market.title)              # Market title
        print(market.historical_status)   # "open" at backtest time
        print(market.was_resolved)        # False if not resolved yet
        print(market.winning_side)        # None if not resolved (prevents lookahead!)
        print(market.side_a.id)          # Token ID for trading
```

**Key Features:**
- Markets with `start_time > backtest_time` are excluded (didn't exist yet)
- `historical_status` reflects status at backtest time, not current
- `winning_side` is `None` if market wasn't resolved (prevents lookahead bias)

## Results

After running a backtest:

```python
result = await dome.run(my_strategy)

# Performance metrics
print(f"Initial Cash: ${result.initial_cash:,.2f}")
print(f"Final Value: ${result.final_value:,.2f}")
print(f"Total Return: {result.total_return_pct:+.2f}%")
print(f"Net Return (after fees): {result.net_return_after_fees_pct:+.2f}%")

# Trading activity
print(f"Total Trades: {len(result.trades)}")
print(f"Total Fees: ${result.total_fees_paid:.2f}")

# Equity curve
for timestamp, value in result.equity_curve:
    print(f"{timestamp}: ${value:.2f}")
```

## Transaction Fees

Fees are **enabled by default** for realistic backtests.

### Polymarket
- **Global Platform**: No fees
- **US Market (QCEX)**: 0.01% taker fee

### Kalshi
Dynamic fees based on contract price: `0.07 × contracts × price × (1 - price)`

**Disable fees:**
```python
dome = DomeBacktestClient({
    "enable_fees": False,  # Disable fees
    ...
})
```

## Kalshi Interest (Optional)

Kalshi offers 4% APY on cash and positions. Enable with:

```python
dome = DomeBacktestClient({
    "enable_interest": True,
    "interest_apy": 0.04,  # 4% APY
    ...
})
```

Interest accrues daily on cash balances and position values.

## API Reference

### DomeBacktestClient

```python
# Initialize
dome = DomeBacktestClient({
    "api_key": "your-key",
    "start_time": 1729800000,
    "end_time": 1729886400,
    "step": 3600,              # Optional
    "initial_cash": 10000,     # Optional
    "enable_fees": True,       # Optional
    "enable_interest": False,  # Optional
    "verbose": False,          # Optional
})

# Run backtest
# strategy_fn should be: async def strategy_fn(dome)
result = await dome.run(strategy_fn)

# Access portfolio
dome.portfolio.cash        # Available cash
dome.portfolio.positions   # Dict[token_id, quantity]

# Polymarket API
await dome.polymarket.markets.get_markets(params)
await dome.polymarket.markets.get_market_price(params)
await dome.polymarket.markets.get_candlesticks(params)
await dome.polymarket.markets.get_orderbooks(params)
await dome.polymarket.markets.create_order({
    "token_id": "...",
    "side": "buy",           # "buy" or "sell"
    "size": "1000000000",
    "price": "0.65",
    "order_type": "GTC"      # "FOK", "FAK", "GTC", "GTD"
})

# Kalshi API
await dome.kalshi.markets.get_markets(params)
await dome.kalshi.orderbooks.get_orderbooks(params)
await dome.kalshi.trades.get_trades(params)
```

### BacktestResult

```python
result.initial_cash              # Starting capital
result.final_value               # Final portfolio value
result.total_return_pct          # Return percentage
result.trades                    # List of all trades
result.equity_curve              # [(timestamp, value), ...]
result.total_fees_paid           # Total fees
result.total_interest_earned     # Total interest (Kalshi)
result.net_return_after_fees_pct # Net return after fees
```

## Rate Limiting

The service includes built-in rate limiting that automatically enforces Dome API tier limits. Rate limit errors are automatically retried with exponential backoff.

### Configuration

Rate limiting is configured via the `rate_limit_tier` parameter (or `rateLimitTier` for camelCase):

```python
dome = DomeBacktestClient({
    "api_key": "...",
    "start_time": ...,
    "end_time": ...,
    "rate_limit_tier": "free",  # "free", "dev", or "enterprise"
})
```

**Available Tiers:**

| Tier | Queries Per Second | Queries Per 10 Seconds |
|------|-------------------|------------------------|
| **Free** (default) | 1 | 10 |
| **Dev** | 100 | 500 |
| **Enterprise** | Custom | Custom |

### Custom Limits (Enterprise)

For Enterprise tier or custom limits, specify `qps` and `per_10s`:

```python
dome = DomeBacktestClient({
    "api_key": "...",
    "start_time": ...,
    "end_time": ...,
    "rate_limit_tier": "enterprise",
    "rate_limit_qps": 200,          # Custom QPS limit
    "rate_limit_per_10s": 1000,      # Custom per-10-second limit
})
```

The rate limiter uses a sliding window approach to track both per-second and per-10-second limits, ensuring compliance with Dome API rate limits across all tiers.
