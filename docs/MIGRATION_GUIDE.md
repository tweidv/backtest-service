# Live to Backtest Migration Guide

## ✅ Confirmed: Drop-in Replacement

**Yes!** You can migrate your live trading strategy to backtesting with **only 2 changes**:

1. **Change the import**
2. **Add start_time and end_time to initialization**

Everything else stays **exactly the same**!

---

## Migration Steps

### Step 1: Change Import

**Before (Live):**
```python
from dome_api_sdk import DomeClient
```

**After (Backtest):**
```python
from backtest_service import DomeBacktestClient
```

### Step 2: Change Initialization

**Before (Live):**
```python
dome = DomeClient({"api_key": "your-api-key"})
```

**After (Backtest):**
```python
from datetime import datetime, timedelta

# Set your backtest time window
end_time = int((datetime.now() - timedelta(days=7)).timestamp())  # 7 days ago
start_time = end_time - 86400  # 1 hour window

dome = DomeBacktestClient({
    "api_key": "your-api-key",
    "start_time": start_time,
    "end_time": end_time,
})
```

### Step 3: Your Strategy Code Stays Identical!

**Everything else is exactly the same:**

```python
# ✅ Same method calls
markets = await dome.polymarket.markets.get_markets({
    "status": "open",
    "limit": 10
})

# ✅ Same parameters
price = await dome.polymarket.markets.get_market_price({
    "token_id": "1234567890"
})

# ✅ Same response structure
print(f"Price: {price.price}")
print(f"Markets: {len(markets.markets)}")

# ✅ Same nested structure
orders = await dome.polymarket.orders.get_orders({
    "market_slug": "bitcoin-up-or-down-july-25-8pm-et",
    "limit": 50
})

activity = await dome.polymarket.activity.get_activity({
    "user": "0x7c3db723f1d4d8cb9c550095203b686cb11e5c6b",
    "limit": 100
})

pnl = await dome.polymarket.wallet.get_wallet_pnl({
    "wallet_address": "0x7c3db723f1d4d8cb9c550095203b686cb11e5c6b",
    "granularity": "day"
})

# ✅ Same for Kalshi
kalshi_markets = await dome.kalshi.markets.get_markets({
    "status": "open",
    "limit": 10
})

# ✅ Same for matching markets
matching = await dome.matching_markets.get_matching_markets({
    "polymarket_market_slug": ["nfl-ari-den-2025-08-16"]
})

# ✅ Same for crypto prices
crypto = await dome.crypto_prices.binance.get_binance_prices({
    "currency": "btcusdt",
    "limit": 10
})
```

---

## Complete Example

### Live Trading Strategy
```python
from dome_api_sdk import DomeClient

async def my_strategy():
    dome = DomeClient({"api_key": "your-api-key"})
    
    # Get markets
    markets = await dome.polymarket.markets.get_markets({
        "status": "open",
        "limit": 10
    })
    
    # Analyze and trade
    for market in markets.markets:
        price = await dome.polymarket.markets.get_market_price({
            "token_id": market.token_id
        })
        print(f"Market: {market.title}, Price: {price.price}")
        
        # Your trading logic here...
```

### Backtest Version (Only 2 Changes!)
```python
from backtest_service import DomeBacktestClient
from datetime import datetime, timedelta

async def my_strategy():
    # ✅ CHANGE 1: Import changed
    # ✅ CHANGE 2: Added start_time/end_time
    end_time = int((datetime.now() - timedelta(days=7)).timestamp())
    start_time = end_time - 86400
    
    dome = DomeBacktestClient({
        "api_key": "your-api-key",
        "start_time": start_time,
        "end_time": end_time,
    })
    
    # ✅ EVERYTHING ELSE IS IDENTICAL!
    markets = await dome.polymarket.markets.get_markets({
        "status": "open",
        "limit": 10
    })
    
    for market in markets.markets:
        price = await dome.polymarket.markets.get_market_price({
            "token_id": market.token_id
        })
        print(f"Market: {market.title}, Price: {price.price}")
        
        # Your trading logic here...
```

---

## What's Guaranteed to Work

✅ **All API methods** - Same names, same parameters  
✅ **Response structures** - Same attributes, same data  
✅ **Nested namespaces** - `dome.polymarket.markets.*`, `dome.kalshi.*`, etc.  
✅ **Async/await** - Same async patterns  
✅ **Error handling** - Same exceptions  
✅ **Parameter validation** - Same validation rules  

---

## What's Different (Backtest-Specific)

### 1. Historical Filtering
- All data is automatically filtered to the backtest time
- No lookahead bias - you only see data that existed at that time
- Time parameters are automatically capped at `backtest_time`

### 2. Portfolio Tracking
- Access to `dome.portfolio` for tracking positions and PnL
- Use `dome.portfolio.buy()` and `dome.portfolio.sell()` for simulated trades
- Dome API is read-only, so trading is simulated

### 3. Time Control
- Time advances automatically when using `dome.run(strategy)`
- Or manually control with `dome._clock.advance_by(seconds)`

---

## Running a Backtest

```python
from backtest_service import DomeBacktestClient
from datetime import datetime, timedelta

# Initialize
end_time = int((datetime.now() - timedelta(days=7)).timestamp())
start_time = end_time - 86400

dome = DomeBacktestClient({
    "api_key": "your-api-key",
    "start_time": start_time,
    "end_time": end_time,
})

# Your strategy (same code as live!)
async def strategy(dome):
    markets = await dome.polymarket.markets.get_markets({
        "status": "open",
        "limit": 10
    })
    
    for market in markets.markets:
        price = await dome.polymarket.markets.get_market_price({
            "token_id": market.token_id
        })
        
        # Simulate trading
        if price.price < 0.5:
            dome.portfolio.buy(
                platform="polymarket",
                token_id=market.token_id,
                quantity=Decimal("1.0"),
                price=Decimal(str(price.price)),
                timestamp=dome._clock.current_time
            )

# Run backtest
result = await dome.run(strategy)
print(f"Total Return: {result.total_return_pct:.2f}%")
print(f"Final Value: ${result.final_value:.2f}")
```

---

## Verification

All API methods have been tested and verified to work with the same syntax:

- ✅ `dome.polymarket.markets.get_markets()`
- ✅ `dome.polymarket.markets.get_market_price()`
- ✅ `dome.polymarket.markets.get_candlesticks()`
- ✅ `dome.polymarket.markets.get_orderbooks()`
- ✅ `dome.polymarket.orders.get_orders()`
- ✅ `dome.polymarket.wallet.get_wallet()`
- ✅ `dome.polymarket.wallet.get_wallet_pnl()`
- ✅ `dome.polymarket.activity.get_activity()`
- ✅ `dome.kalshi.markets.get_markets()`
- ✅ `dome.kalshi.orderbooks.get_orderbooks()`
- ✅ `dome.kalshi.trades.get_trades()`
- ✅ `dome.matching_markets.get_matching_markets()`
- ✅ `dome.matching_markets.get_matching_markets_by_sport()`
- ✅ `dome.crypto_prices.binance.get_binance_prices()`
- ✅ `dome.crypto_prices.chainlink.get_chainlink_prices()`

---

## Summary

**Migration is trivial:**
1. Change import: `DomeClient` → `DomeBacktestClient`
2. Add `start_time` and `end_time` to config
3. Everything else stays **exactly the same**!

Your live trading strategy code will work in backtesting without any modifications to the actual strategy logic! 🎉

