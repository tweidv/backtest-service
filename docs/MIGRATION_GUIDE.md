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
- Dome API is **read-only** (data only)
- Mock `create_order()`, `buy()`, and `sell()` methods are included for simulation/forward compatibility
- For actual trading, use `PolymarketBacktestClient` or `KalshiBacktestClient` with native SDKs

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

## Using Official Native SDKs (For Trading)

**Dome is read-only** - it only provides data access. For actual order creation and trading, use the native SDK backtest clients as drop-in replacements for the official SDKs.

### Important Note

- **Dome** (`DomeBacktestClient`) is **read-only** - only for reading market data, prices, orderbooks, etc.
- **Dome's `create_order()`, `buy()`, `sell()`** are **mock/simulation methods** included for completeness and forward compatibility (Dome itself doesn't support trading)
- **Native SDK backtest clients** (`PolymarketBacktestClient`, `KalshiBacktestClient`) are for actual trading using the official SDKs
- Use Dome for data, native SDK clients for trading

### Polymarket Native SDK (`py-clob-client`)

**If your strategy uses `py-clob-client` directly:**

**Live:**
```python
from py_clob_client import ClobClient

client = ClobClient(api_key="...")
order = await client.create_order(
    token_id="0x123...",
    side="YES",
    size="1000000000",
    price="0.65",
    order_type="GTC"
)
```

**Backtest:**
```python
from backtest_service.native import PolymarketBacktestClient

client = PolymarketBacktestClient({
    "dome_api_key": "...",  # Uses Dome for historical data
    "start_time": 1729800000,
    "end_time": 1729886400,
    "initial_cash": 10000,
})

# Same code! ✅ Just swap the import
order = await client.create_order(
    token_id="0x123...",
    side="YES",
    size="1000000000",
    price="0.65",
    order_type="GTC"
)
```

### Kalshi Native SDK (`kalshi`)

**If your strategy uses `kalshi` SDK directly:**

**Live:**
```python
from kalshi import KalshiClient

client = KalshiClient(api_key="...")
order = await client.create_order(
    ticker="KXNFLGAME-25AUG16ARIDEN-ARI",
    side="yes",
    action="buy",
    count=100,
    order_type="limit",
    yes_price=75
)
```

**Backtest:**
```python
from backtest_service.native import KalshiBacktestClient

client = KalshiBacktestClient({
    "dome_api_key": "...",  # Uses Dome for historical data
    "start_time": 1729800000,
    "end_time": 1729886400,
    "initial_cash": 10000,
})

# Same code! ✅ Just swap the import
order = await client.create_order(
    ticker="KXNFLGAME-25AUG16ARIDEN-ARI",
    side="yes",
    action="buy",
    count=100,
    order_type="limit",
    yes_price=75
)
```

## Order Types Supported

All backtest clients support realistic order types:

- **MARKET** - Fills immediately at best available price
- **LIMIT** - Fills if price is marketable, otherwise queues
- **FOK** (Fill-or-Kill) - Fills completely or rejects
- **GTC** (Good-Till-Cancel) - Persists until filled or cancelled
- **GTD** (Good-Till-Date) - Persists until expiration or filled

Order matching uses historical orderbook data from Dome API to simulate realistic fills.

## Summary

**Migration is trivial:**
1. **For Dome API users**: Change import `DomeClient` → `DomeBacktestClient`, add `start_time`/`end_time`
2. **For native SDK users**: Change import (e.g., `ClobClient` → `PolymarketBacktestClient`), add config
3. Everything else stays **exactly the same**!

Your live trading strategy code will work in backtesting without any modifications to the actual strategy logic! 🎉

**Choose your approach:**
- **Dome API** (`DomeBacktestClient`) - Read-only data access for both platforms (markets, prices, orderbooks, etc.)
- **Native SDKs** (`PolymarketBacktestClient`, `KalshiBacktestClient`) - For actual order creation and trading (Dome is read-only)

**Typical workflow**: Use Dome for data, native SDK clients for trading.

