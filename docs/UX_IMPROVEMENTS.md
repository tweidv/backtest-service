# UX Improvements Proposal

## Goals
- Stream progress in real-time
- Show simulated API calls
- Better visibility into what's happening
- Progress indicators
- Optional verbose/debug mode

## Implementation Plan

### 1. Verbose/Debug Mode
Add `verbose` parameter to `DomeBacktestClient`:
```python
dome = DomeBacktestClient({
    "api_key": "...",
    "verbose": True,  # Show API calls, progress, etc.
    "log_level": "INFO"  # DEBUG, INFO, WARNING, ERROR
})
```

### 2. API Call Logging
Show each API call being made:
```
[API] GET /polymarket/markets?status=open&limit=10
[API] Response: 50 markets found
[API] GET /polymarket/market-price/{token_id}?at_time=1729800000
[API] Response: price=0.65
```

### 3. Progress Streaming
Show tick-by-tick progress:
```
[Tick 1/56] 2024-11-01 00:00:00 | Cash: $10,000.00 | Value: $10,000.00
  → Fetching markets...
  → Found 50 markets
  → Analyzing markets...
  → Trade executed: BUY 100 @ $0.65
[Tick 2/56] 2024-11-01 06:00:00 | Cash: $9,935.00 | Value: $10,000.00
...
```

### 4. Callback System
Allow users to hook into events:
```python
async def on_tick(dome, portfolio):
    print(f"Tick: {dome._clock.current_time}")

async def on_api_call(endpoint, params, response):
    print(f"API: {endpoint}")

dome = DomeBacktestClient({
    "api_key": "...",
    "on_tick": on_tick,
    "on_api_call": on_api_call,
})
```

### 5. Progress Bar
Optional progress bar for long backtests:
```
Progress: [████████░░░░░░░░] 50% (28/56 ticks)
```

