# Backtest Service

A backtesting framework for **Polymarket** and **Kalshi** prediction markets using the [Dome API](https://domeapi.io). Test your trading strategies on historical data without placing real orders.

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
            # Buy tokens (simulated)
            dome.polymarket.buy(
                market.side_a.id,
                quantity=100,
                price=price_data.price
            )

# Run backtest
result = await dome.run(my_strategy)
print(f"Return: {result.total_return_pct:.2f}%")
print(f"Final Value: ${result.final_value:.2f}")
```

## Installation

```bash
pip install dome-api-sdk
git clone https://github.com/yourusername/backtest-service.git
cd backtest-service
pip install -e .
```

### Environment Variables

The library supports loading your API key from environment variables for convenience. Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key
DOME_API_KEY=your-dome-api-key-here
```

The API key will be automatically loaded from the `DOME_API_KEY` environment variable if not provided in the config. You can still pass it explicitly in the config if you prefer.

Get your Dome API key from [domeapi.io](https://domeapi.io).

## Key Features

- **🔄 Drop-in Replacement** — Same API as `DomeClient`, just swap the import
- **📊 Historical Data** — No local storage needed, uses Dome API's historical endpoints
- **🎯 No Lookahead Bias** — Markets are filtered to only include data available at backtest time
- **💰 Realistic Simulation** — Transaction fees, orderbook matching, portfolio tracking
- **📈 Progress Streaming** — See API calls and progress in real-time with verbose mode
- **🔌 Multi-Platform** — Support for Polymarket and Kalshi

## How It Works

The framework automatically injects historical timestamps into all API calls, replaying market data as if you were trading in the past. Your strategy code stays the same — just swap `DomeClient` for `DomeBacktestClient`.

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
    "step": 3600,                         # Optional: seconds between ticks (default: 3600)
    "initial_cash": 10000,                # Optional: starting capital (default: 10000)
    "enable_fees": True,                  # Optional: transaction fees (default: True)
    "enable_interest": False,             # Optional: Kalshi interest (default: False)
    "verbose": False,                     # Optional: show progress (default: False)
    "log_level": "INFO",                  # Optional: DEBUG, INFO, WARNING, ERROR
})
```

### Verbose Mode (See What's Happening)

Enable `verbose=True` to see real-time progress:

```python
dome = DomeBacktestClient({
    "api_key": "...",
    "start_time": ...,
    "end_time": ...,
    "verbose": True,  # Enable streaming output
    "log_level": "INFO",  # DEBUG for more detail
})

# Output:
# [Tick 1/56] 2024-11-01 00:00:00 | Cash: $10,000.00 | Value: $10,000.00 | Positions: 0
#   [API] 00:00:00 polymarket.PolymarketMarketsNamespace.get_markets({'status': 'open'})
#     -> 50 markets
#   [API] 00:00:01 polymarket.PolymarketMarketsNamespace.get_market_price({'token_id': '...'})
#     -> price=0.65
```

See [docs/UX_FEATURES.md](docs/UX_FEATURES.md) for more details.

## Trading

### Using DomeBacktestClient (Simple Trading)

For simple buy/sell operations:

```python
async def strategy(dome):
    price_data = await dome.polymarket.markets.get_market_price({
        "token_id": "0x123..."
    })
    
    # Buy tokens
    dome.polymarket.buy(
        token_id="0x123...",
        quantity=100,
        price=price_data.price
    )
    
    # Sell tokens
    dome.polymarket.sell(
        token_id="0x123...",
        quantity=50,
        price=0.70
    )
```

### Using Native SDK Clients (Advanced Orders)

For advanced order types (limit, market, GTC, GTD):

```python
from backtest_service.native import PolymarketBacktestClient

client = PolymarketBacktestClient({
    "dome_api_key": "your-key",
    "start_time": ...,
    "end_time": ...,
    "initial_cash": 10000,
})

# Create limit order
order = await client.create_order(
    token_id="0x123...",
    side="YES",
    size="1000000000",  # Base units (1e18)
    price="0.65",
    order_type="GTC"
)
```

See [docs/MIGRATION_GUIDE.md](docs/MIGRATION_GUIDE.md) for full examples.

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
result = await dome.run(strategy_fn)

# Access portfolio
dome.portfolio.cash        # Available cash
dome.portfolio.positions   # Dict[token_id, quantity]

# Polymarket API
await dome.polymarket.markets.get_markets(params)
await dome.polymarket.markets.get_market_price(params)
await dome.polymarket.markets.get_candlesticks(params)
await dome.polymarket.markets.get_orderbooks(params)

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

## Examples

See the `tests/` directory for example strategies:
- `test_advanced_strategy.py` - Momentum strategy example
- `test_full_backtest.py` - Complete backtest with SMA crossover
- `test_arbitrage_discovery.py` - Arbitrage finding strategy

## Converting Live Code to Backtest

**Just 2 changes needed:**

1. **Change import:**
   ```python
   # Live
   from dome_api_sdk import DomeClient
   
   # Backtest
   from backtest_service import DomeBacktestClient
   ```

2. **Add time window:**
   ```python
   # Live
   dome = DomeClient({"api_key": "..."})
   
   # Backtest
   dome = DomeBacktestClient({
       "api_key": "...",
       "start_time": int(datetime(2024, 11, 1).timestamp()),
       "end_time": int(datetime(2024, 11, 2).timestamp()),
   })
   ```

**That's it!** Your strategy code stays exactly the same.

## Limitations

### Kalshi Support

Kalshi support has some limitations due to Dome API constraints:
- Portfolio valuation uses orderbook data (may be less accurate than Polymarket)
- Some historical data may be incomplete

For full Kalshi backtesting, consider using `KalshiBacktestClient` from `backtest_service.native`.

## Rate Limiting

The service includes built-in rate limiting (1.1s between API calls) to comply with Dome API limits. Rate limit errors are automatically retried with exponential backoff.

## License

MIT

## Contributing

Contributions welcome! Please open an issue or pull request.
