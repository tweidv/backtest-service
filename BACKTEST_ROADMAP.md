# Backtest Service Roadmap

## Overview

This document outlines the roadmap for expanding the backtest service to cover additional Dome API functions that are valuable for backtesting prediction market strategies.

## Current Implementation Status

### ✅ Implemented Features

**Polymarket:**
- `get_markets()` - Historical market discovery with status filtering
- `get_market_price()` - Current/historical price lookup
- `get_orderbook_history()` - Historical orderbook snapshots
- `get_trade_history()` - Historical trade data (orders)
- `buy()` / `sell()` - Simulated order execution

**Kalshi:**
- `get_markets()` - Historical market discovery with status filtering
- `get_orderbooks()` - Historical orderbook snapshots
- `buy()` / `sell()` - Simulated order execution

**Core Infrastructure:**
- `SimulationClock` - Time management for backtests
- `Portfolio` - Position tracking and PnL calculation
- `DomeBacktestClient` - Main client interface
- `BacktestRunner` - Backtest execution engine
- Historical filtering logic (markets that existed at backtest time)

---

## Priority 1: Critical for Advanced Backtesting

### 1.1 Candlestick Data Support
**Status:** Not Implemented  
**API Endpoint:** `/polymarket/candlesticks/{condition_id}`  
**Priority:** HIGH

**Why it's needed:**
- Technical analysis strategies require OHLCV data
- Volume analysis and price patterns
- Better price interpolation between trades
- Standard format for most trading strategies

**Implementation Requirements:**
- Add `get_candlesticks()` to `PlatformAPI`
- Support intervals: 1m, 1h, 1d (with range limits)
- Historical filtering: only return candlesticks up to `clock.current_time`
- Handle pagination for long time ranges

**Use Cases:**
- Moving average strategies
- Volume-based entry/exit signals
- Pattern recognition (support/resistance)
- Volatility analysis

---

### 1.2 Enhanced Trade History (Orders) Filtering
**Status:** Partially Implemented  
**API Endpoint:** `/polymarket/orders`  
**Priority:** HIGH

**Current Gap:**
- Currently uses `get_trade_history()` but API has more comprehensive `/polymarket/orders` endpoint
- Missing user-based filtering (track specific traders)
- Missing condition_id filtering
- Missing proper pagination handling

**Implementation Requirements:**
- Add `get_orders()` method to `PlatformAPI`
- Support filtering by: user, condition_id, token_id, market_slug, time range
- Historical filtering: cap `end_time` at `clock.current_time`
- Proper pagination support

**Use Cases:**
- Copy trading strategies (follow specific traders)
- Market maker analysis
- Liquidity analysis
- Order flow analysis

---

### 1.3 Kalshi Trade History
**Status:** Not Implemented  
**API Endpoint:** `/kalshi/trades`  
**Priority:** HIGH

**Why it's needed:**
- Complete parity with Polymarket features
- Cross-platform arbitrage strategies
- Kalshi-specific trading patterns

**Implementation Requirements:**
- Add `get_trades()` to `KalshiAPI`
- Support filtering by ticker, time range
- Historical filtering: cap `end_time` at `clock.current_time`
- Handle pagination

**Use Cases:**
- Cross-platform arbitrage
- Kalshi-specific strategies
- Market comparison analysis

---

## Priority 2: Important for Strategy Development

### 2.1 Activity Tracking (MERGE, SPLIT, REDEEM)
**Status:** Not Implemented  
**API Endpoint:** `/polymarket/activity`  
**Priority:** MEDIUM

**Why it's needed:**
- Track market resolution events
- Understand when markets close and resolve
- Calculate realized PnL from redeems
- Model market lifecycle events

**Implementation Requirements:**
- Add `get_activity()` to `PlatformAPI`
- Filter by user, market_slug, condition_id, time range
- Historical filtering: cap `end_time` at `clock.current_time`
- Support MERGE, SPLIT, REDEEM activity types

**Use Cases:**
- Automatic position closing on market resolution
- Realized PnL calculation from redeems
- Market lifecycle tracking
- Strategy validation (did market resolve as expected?)

---

### 2.2 Wallet Information
**Status:** Not Implemented  
**API Endpoint:** `/polymarket/wallet/{wallet_address}`  
**Priority:** MEDIUM

**Why it's needed:**
- Track wallet metrics during backtest
- Compare strategy performance to real wallets
- Validate portfolio state against API data

**Implementation Requirements:**
- Add `get_wallet()` to `PlatformAPI`
- Support `with_metrics=true` for trading statistics
- Historical context: what was wallet state at backtest time?

**Use Cases:**
- Performance benchmarking
- Strategy validation
- Portfolio reconciliation

---

### 2.3 Wallet PnL Tracking
**Status:** Not Implemented  
**API Endpoint:** `/polymarket/wallet/pnl/{wallet_address}`  
**Priority:** MEDIUM

**Why it's needed:**
- Compare backtest PnL to realized PnL from API
- Validate PnL calculations
- Understand realized vs unrealized gains

**Implementation Requirements:**
- Add `get_wallet_pnl()` to `PlatformAPI`
- Support granularity: day, week, month, year, all
- Historical filtering: cap `end_time` at `clock.current_time`
- Note: API tracks realized PnL only (from sells/redeems)

**Use Cases:**
- PnL validation
- Performance comparison
- Realized vs unrealized analysis

---

## Priority 3: Advanced Features

### 3.1 Matching Markets (Cross-Platform Discovery)
**Status:** Not Implemented  
**API Endpoint:** `/matching-markets/sports/`  
**Priority:** MEDIUM-LOW

**Why it's needed:**
- Find equivalent markets across Polymarket and Kalshi
- Cross-platform arbitrage strategies
- Market discovery for sports events

**Implementation Requirements:**
- Add `matching_markets` namespace to `DomeBacktestClient`
- Support `get_matching_markets()` by Polymarket slug or Kalshi ticker
- Support `get_matching_markets_by_sport()` by sport and date
- Historical filtering: only show markets that existed at backtest time

**Use Cases:**
- Cross-platform arbitrage
- Sports betting strategies
- Market discovery automation

---

### 3.2 Crypto Price Data
**Status:** Not Implemented  
**API Endpoints:** `/crypto-prices/binance`, `/crypto-prices/chainlink`  
**Priority:** LOW

**Why it's needed:**
- Correlate crypto markets with prediction markets
- External data for strategy signals
- Market correlation analysis

**Implementation Requirements:**
- Add `crypto_prices` namespace to `DomeBacktestClient`
- Support Binance and Chainlink price feeds
- Historical filtering: cap `end_time` at `clock.current_time`
- Support time range queries

**Use Cases:**
- Correlation strategies
- External signal integration
- Market analysis

---

## Priority 4: Infrastructure Improvements

### 4.1 Enhanced Orderbook Support
**Status:** Partially Implemented  
**Priority:** MEDIUM

**Current Gap:**
- Basic orderbook history exists
- Missing depth analysis utilities
- Missing spread calculation helpers
- Missing liquidity metrics

**Improvements Needed:**
- Add helper methods: `get_best_bid()`, `get_best_ask()`, `get_spread()`
- Add depth analysis: `get_liquidity_at_price()`, `get_total_depth()`
- Add orderbook snapshot comparison utilities

**Use Cases:**
- Market making strategies
- Slippage estimation
- Liquidity analysis

---

### 4.2 Market Data Caching
**Status:** Not Implemented  
**Priority:** MEDIUM

**Why it's needed:**
- Reduce API calls during backtests
- Faster iteration on strategies
- Cost savings on API usage

**Implementation Requirements:**
- Add caching layer for market data
- Cache key: `{endpoint}_{params}_{at_time}`
- Configurable cache TTL
- Optional: persistent cache (file/database)

**Use Cases:**
- Faster backtest execution
- Reduced API costs
- Strategy iteration speed

---

### 4.3 Historical Data Validation
**Status:** Not Implemented  
**Priority:** LOW

**Why it's needed:**
- Ensure backtest accuracy
- Detect data quality issues
- Validate historical filtering logic

**Implementation Requirements:**
- Add validation checks:
  - Market status consistency
  - Price continuity
  - Time range validity
  - Data completeness

**Use Cases:**
- Quality assurance
- Debugging backtest issues
- Data integrity checks

---

## Priority 5: WebSocket Support (Forward Testing)

### 5.1 WebSocket Integration
**Status:** Not Implemented  
**API:** WebSocket endpoints for real-time order data  
**Priority:** LOW (Not for backtesting, but for forward testing)

**Why it's needed:**
- Forward testing with live data
- Real-time strategy execution
- Paper trading capabilities

**Note:** This is separate from backtesting but could be valuable for the overall service.

---

## Implementation Phases

### Phase 1: Core Data Access (Weeks 1-2)
**Goal:** Enable technical analysis and advanced order tracking

1. ✅ Candlestick data support (`get_candlesticks()`)
2. ✅ Enhanced trade history (`get_orders()` with full filtering)
3. ✅ Kalshi trade history (`get_trades()`)

**Deliverables:**
- All Priority 1 features implemented
- Tests for new endpoints
- Documentation updates

---

### Phase 2: Activity & Wallet Tracking (Weeks 3-4)
**Goal:** Enable market lifecycle tracking and PnL validation

1. ✅ Activity tracking (`get_activity()`)
2. ✅ Wallet information (`get_wallet()`)
3. ✅ Wallet PnL (`get_wallet_pnl()`)

**Deliverables:**
- Market resolution tracking
- PnL validation capabilities
- Portfolio reconciliation tools

---

### Phase 3: Advanced Features (Weeks 5-6)
**Goal:** Enable cross-platform strategies and external data

1. ✅ Matching markets support
2. ✅ Crypto price data integration
3. ✅ Enhanced orderbook utilities

**Deliverables:**
- Cross-platform arbitrage capabilities
- External data integration
- Improved orderbook analysis

---

### Phase 4: Infrastructure (Weeks 7-8)
**Goal:** Performance and reliability improvements

1. ✅ Market data caching
2. ✅ Historical data validation
3. ✅ Performance optimizations

**Deliverables:**
- Faster backtest execution
- Data quality assurance
- Improved developer experience

---

## Testing Strategy

For each new feature:
1. **Unit Tests:** Test historical filtering logic
2. **Integration Tests:** Test against real API with historical data
3. **Strategy Tests:** Create example strategies using new features
4. **Edge Cases:** Test time boundaries, missing data, pagination

---

## Documentation Needs

For each new feature:
1. **API Documentation:** Method signatures and parameters
2. **Usage Examples:** Simple strategy examples
3. **Historical Filtering Notes:** How time filtering works
4. **Migration Guide:** If replacing existing functionality

---

## Notes

### Historical Filtering Principles

All new endpoints must:
- Cap `end_time` at `clock.current_time` (don't see future data)
- Filter results to only show data that existed at backtest time
- Handle edge cases (markets that didn't exist yet, closed markets, etc.)

### Rate Limiting

Current implementation uses `rate_limit` parameter (default 1.1s between calls).
- Consider adaptive rate limiting based on API tier
- Add rate limit error handling
- Consider batch requests where possible

### Error Handling

- Handle API errors gracefully
- Provide clear error messages for historical filtering issues
- Log warnings for data quality issues

---

## Success Metrics

- **Coverage:** All Priority 1 and 2 features implemented
- **Performance:** Backtests complete in reasonable time (< 5 min for 1 week)
- **Reliability:** 99%+ success rate on API calls
- **Usability:** Clear examples for each new feature
- **Documentation:** Complete API reference and usage guides

---

## Future Considerations

- **Database Backend:** Store historical data locally for faster access
- **Parallel Execution:** Run multiple backtests in parallel
- **Strategy Marketplace:** Share and discover strategies
- **Visualization:** Charts and graphs for backtest results
- **ML Integration:** Use historical data for ML model training

