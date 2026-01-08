# UX Features - Streaming Progress & API Call Visibility

The backtest service now includes built-in UX improvements for better visibility into what's happening during backtests.

## Quick Start

Enable verbose mode to see streaming progress and API calls:

```python
from backtest_service import DomeBacktestClient
from datetime import datetime

dome = DomeBacktestClient({
    "api_key": "your-key",
    "start_time": int(datetime(2024, 11, 1).timestamp()),
    "end_time": int(datetime(2024, 11, 2).timestamp()),
    "verbose": True,  # Enable streaming output
    "log_level": "INFO",  # DEBUG, INFO, WARNING, ERROR
})

result = await dome.run(my_strategy)
```

## Features

### 1. Verbose Mode

Shows real-time progress during backtest execution:

```
[Tick 1/56] 2024-11-01 00:00:00 | Cash: $10,000.00 | Value: $10,000.00 | Positions: 0
  [API] 00:00:00 polymarket.PolymarketMarketsNamespace.get_markets({'status': 'open', 'limit': 10})
    -> 50 markets
  [API] 00:00:01 polymarket.PolymarketMarketsNamespace.get_market_price({'token_id': '0x123...'})
    -> price=0.65

[Tick 2/56] 2024-11-01 06:00:00 | Cash: $9,935.00 | Value: $10,000.00 | Positions: 1
  ...
```

### 2. Log Levels

Control how much detail you see:

- **DEBUG**: Shows all API calls with full details
- **INFO**: Shows API calls with summaries (default)
- **WARNING**: Only warnings and errors
- **ERROR**: Only errors

```python
dome = DomeBacktestClient({
    "api_key": "...",
    "verbose": True,
    "log_level": "DEBUG",  # Most verbose
})
```

### 3. Callbacks

Hook into backtest events:

```python
async def on_tick(dome, portfolio):
    """Called at the start of each tick"""
    print(f"Tick at {dome._clock.current_time}")

async def on_api_call(endpoint, params, response):
    """Called after each API call"""
    print(f"API: {endpoint} -> {len(response.markets) if hasattr(response, 'markets') else 'OK'}")

dome = DomeBacktestClient({
    "api_key": "...",
    "on_tick": on_tick,
    "on_api_call": on_api_call,
})
```

## Example Output

With `verbose=True` and `log_level="INFO"`:

```
[Tick 1/4] 2024-11-01 00:00:00 | Cash: $10,000.00 | Value: $10,000.00 | Positions: 0
  [API] 00:00:00 polymarket.PolymarketMarketsNamespace.get_markets({'status': 'open', 'limit': 5})
    -> 50 markets
  [API] 00:00:01 polymarket.PolymarketMarketsNamespace.get_market_price({'token_id': '0x123...'})
    -> price=0.65
  [API] 00:00:02 polymarket.PolymarketMarketsNamespace.get_market_price({'token_id': '0x456...'})
    -> price=0.35

[Tick 2/4] 2024-11-01 12:00:00 | Cash: $9,935.00 | Value: $10,000.00 | Positions: 1
  [API] 12:00:00 polymarket.PolymarketMarketsNamespace.get_markets({'status': 'open', 'limit': 5})
    -> 50 markets

[Tick 3/4] 2024-11-02 00:00:00 | Cash: $9,870.00 | Value: $10,050.00 | Positions: 2
  ...

[Tick 4/4] 2024-11-02 12:00:00 | Cash: $9,805.00 | Value: $10,100.00 | Positions: 2
```

## Benefits

1. **See what's happening**: No more silent waiting - see every API call
2. **Debug strategies**: Understand exactly what your strategy is doing
3. **Monitor progress**: Track progress through long backtests
4. **Identify bottlenecks**: See which API calls are slow
5. **Verify correctness**: Confirm API calls are using correct historical timestamps

## Performance

Verbose mode adds minimal overhead - it only prints when enabled. For production backtests, you can disable it:

```python
dome = DomeBacktestClient({
    "api_key": "...",
    "verbose": False,  # Silent mode (default)
})
```

