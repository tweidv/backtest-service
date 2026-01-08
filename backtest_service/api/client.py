"""Main backtest client that replays historical data."""

import os
from decimal import Decimal
from typing import Callable, Optional

from dome_api_sdk import DomeClient

from ..simulation.clock import SimulationClock
from ..simulation.portfolio import Portfolio
from .polymarket import PolymarketNamespace
from .kalshi import KalshiNamespace
from .matching_markets import MatchingMarketsNamespace
from .crypto_prices import CryptoPricesNamespace


class DomeBacktestClient:
    """Drop-in replacement for DomeClient that replays historical data"""
    
    def __init__(self, config_or_api_key, clock=None, portfolio=None):
        """
        Initialize backtest client.
        
        New style (recommended):
            dome = DomeBacktestClient({
                "api_key": "your-key",
                "start_time": 1729800000,
                "end_time": 1729886400,
                "step": 3600,  # optional
                "initial_cash": 10000,  # optional
            })
        
        Old style (for backward compatibility with BacktestRunner):
            dome = DomeBacktestClient(api_key, clock, portfolio)
        """
        # Support both new (config dict) and old (api_key, clock, portfolio) signatures
        if isinstance(config_or_api_key, dict):
            # New style: config dict
            config = config_or_api_key
            self.api_key = config.get("api_key") or config.get("apiKey")
            # Auto-load from environment if not provided in config
            if not self.api_key:
                self.api_key = os.environ.get("DOME_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "api_key is required. Provide it in config or set DOME_API_KEY environment variable."
                )
            
            self.start_time = config.get("start_time") or config.get("startTime")
            self.end_time = config.get("end_time") or config.get("endTime")
            if self.start_time is None or self.end_time is None:
                raise ValueError("start_time and end_time are required in config")
            
            self.step = config.get("step", 3600)
            self.initial_cash = Decimal(str(config.get("initial_cash", config.get("initialCash", 10000))))
            
            # Fee and interest configuration
            self.enable_fees = config.get("enable_fees", True)
            self.enable_interest = config.get("enable_interest", False)  # Kalshi only
            self.interest_apy = Decimal(str(config.get("interest_apy", "0.04")))  # 4% APY default
            
            # UX/Logging configuration
            self.verbose = config.get("verbose", False)
            self.log_level = config.get("log_level", "INFO")  # DEBUG, INFO, WARNING, ERROR
            self.on_tick = config.get("on_tick", None)  # Callback: async fn(dome, portfolio)
            self.on_api_call = config.get("on_api_call", None)  # Callback: async fn(endpoint, params, response)
            
            # Create internal components
            self._clock = SimulationClock(self.start_time)
            self._portfolio = Portfolio(
                self.initial_cash,
                enable_fees=self.enable_fees,
                enable_interest=self.enable_interest,
                interest_apy=self.interest_apy
            )
        else:
            # Old style: api_key, clock, portfolio (for backward compatibility)
            if clock is None or portfolio is None:
                raise ValueError("For old-style initialization, clock and portfolio are required")
            self.api_key = config_or_api_key
            # Auto-load from environment if None or empty string
            if not self.api_key:
                self.api_key = os.environ.get("DOME_API_KEY")
            if not self.api_key:
                raise ValueError(
                    "api_key is required. Provide it as argument or set DOME_API_KEY environment variable."
                )
            self._clock = clock
            self._portfolio = portfolio
            self.start_time = clock.current_time
            self.end_time = None  # Will be set by run() or BacktestRunner
            self.step = 3600
            self.initial_cash = portfolio.cash
            # Default UX settings for old style
            self.verbose = False
            self.log_level = "INFO"
            self.on_tick = None
            self.on_api_call = None
        
        self._real_client = DomeClient({"api_key": self.api_key})
        
        # Expose portfolio for strategy access
        self.portfolio = self._portfolio
        
        # Setup platform APIs - matches Dome's nested structure exactly
        self.polymarket = PolymarketNamespace(self._real_client, self._clock, self._portfolio)
        self.kalshi = KalshiNamespace(self._real_client, self._clock, self._portfolio)
        self.matching_markets = MatchingMarketsNamespace(self._real_client, self._clock, self._portfolio)
        self.crypto_prices = CryptoPricesNamespace(self._real_client, self._clock, self._portfolio)
        
        # Set verbose/logging on all namespace APIs (they inherit from BasePlatformAPI)
        # Note: This will be called again in run() after reset, but setting here for immediate use
        if isinstance(config_or_api_key, dict):
            self._set_verbose_on_namespaces()
    
    def _set_verbose_on_namespaces(self):
        """Set verbose/logging settings on all API namespaces."""
        # Polymarket
        for attr in ['markets', 'orders', 'wallet', 'activity']:
            if hasattr(self.polymarket, attr):
                api_obj = getattr(self.polymarket, attr)
                if hasattr(api_obj, '_verbose'):
                    api_obj._verbose = self.verbose
                    api_obj._log_level = self.log_level
                    api_obj._on_api_call = self.on_api_call
                    api_obj._dome_client = self
        
        # Kalshi
        for attr in ['markets', 'orderbooks', 'trades']:
            if hasattr(self.kalshi, attr):
                api_obj = getattr(self.kalshi, attr)
                if hasattr(api_obj, '_verbose'):
                    api_obj._verbose = self.verbose
                    api_obj._log_level = self.log_level
                    api_obj._on_api_call = self.on_api_call
                    api_obj._dome_client = self
        
        # Matching markets
        if hasattr(self.matching_markets, '_verbose'):
            self.matching_markets._verbose = self.verbose
            self.matching_markets._log_level = self.log_level
            self.matching_markets._on_api_call = self.on_api_call
            self.matching_markets._dome_client = self
        
        # Crypto prices
        for attr in ['binance', 'chainlink']:
            if hasattr(self.crypto_prices, attr):
                api_obj = getattr(self.crypto_prices, attr)
                if hasattr(api_obj, '_verbose'):
                    api_obj._verbose = self.verbose
                    api_obj._log_level = self.log_level
                    api_obj._on_api_call = self.on_api_call
                    api_obj._dome_client = self
    
    async def run(self, strategy: Callable, get_prices: Optional[Callable] = None, end_time: Optional[int] = None):
        """
        Run backtest with your strategy.
        
        Args:
            strategy: async function that takes (dome) or (dome, portfolio)
                     Your existing strategy code - uses dome.polymarket.markets.*, dome.kalshi.markets.*, etc.
                     Matches Dome's exact structure: dome.polymarket.markets.get_markets(), etc.
            get_prices: optional function(dome) -> {token_id: price}
                       If not provided, auto-detects from portfolio positions
            end_time: optional Unix timestamp to override config end_time
                      (useful for old-style initialization)
        
        Returns:
            BacktestResult with performance metrics
            
        Example:
            async def my_strategy(dome):
                price = await dome.polymarket.markets.get_market_price({"token_id": "..."})
                if dome.portfolio.cash > 100:
                    dome.portfolio.buy(...)  # Trading methods are on portfolio
            
            result = await dome.run(my_strategy)
            print(f"Return: {result.total_return_pct:.2f}%")
        """
        from ..models.result import BacktestResult
        import inspect
        
        # Use provided end_time or fall back to config
        effective_end_time = end_time if end_time is not None else self.end_time
        if effective_end_time is None:
            raise ValueError("end_time must be provided either in config or as parameter to run()")
        
        # Reset clock and portfolio for fresh run
        self._clock = SimulationClock(self.start_time)
        self._portfolio = Portfolio(
            self.initial_cash,
            enable_fees=self.enable_fees,
            enable_interest=self.enable_interest,
            interest_apy=self.interest_apy
        )
        self.portfolio = self._portfolio  # Update reference
        self.polymarket = PolymarketNamespace(self._real_client, self._clock, self._portfolio)
        self.kalshi = KalshiNamespace(self._real_client, self._clock, self._portfolio)
        self.matching_markets = MatchingMarketsNamespace(self._real_client, self._clock, self._portfolio)
        self.crypto_prices = CryptoPricesNamespace(self._real_client, self._clock, self._portfolio)
        
        # Re-apply verbose settings after reset
        self._set_verbose_on_namespaces()
        
        # Auto-detect get_prices if not provided
        if get_prices is None:
            async def auto_get_prices(dome):
                """Auto-detect prices for all positions in portfolio"""
                prices = {}
                for position_key in dome.portfolio.positions.keys():
                    try:
                        # Try polymarket first
                        data = await dome.polymarket.markets.get_market_price({"token_id": position_key})
                        prices[position_key] = Decimal(str(data.price))
                    except:
                        try:
                            # Try kalshi - check if this is a Kalshi position (format: "ticker:YES" or "ticker:NO")
                            if ":" in position_key:
                                # Kalshi position with side tracking
                                ticker, side = position_key.rsplit(":", 1)
                                # Get orderbook to extract price
                                orderbook_data = await dome.kalshi.orderbooks.get_orderbooks({
                                    "ticker": ticker,
                                    "end_time": dome._clock.current_time * 1000,  # milliseconds
                                    "limit": 1
                                })
                                
                                if hasattr(orderbook_data, 'snapshots') and orderbook_data.snapshots:
                                    snapshot = orderbook_data.snapshots[0]
                                    # Extract price based on side
                                    if side.upper() == "YES":
                                        # For YES: get NO bids and convert to YES price
                                        if hasattr(snapshot, 'orderbook'):
                                            ob = snapshot.orderbook
                                        elif isinstance(snapshot, dict):
                                            ob = snapshot.get('orderbook', {})
                                        else:
                                            ob = {}
                                        
                                        no_bids = ob.get('no', []) if isinstance(ob, dict) else []
                                        if no_bids:
                                            no_price_cents = Decimal(str(no_bids[0][0]))
                                            yes_price = Decimal(1) - (no_price_cents / Decimal(100))
                                            prices[position_key] = yes_price
                                    else:  # NO
                                        # For NO: get YES bids and convert to NO price
                                        if hasattr(snapshot, 'orderbook'):
                                            ob = snapshot.orderbook
                                        elif isinstance(snapshot, dict):
                                            ob = snapshot.get('orderbook', {})
                                        else:
                                            ob = {}
                                        
                                        yes_bids = ob.get('yes', []) if isinstance(ob, dict) else []
                                        if yes_bids:
                                            yes_price_cents = Decimal(str(yes_bids[0][0]))
                                            no_price = Decimal(1) - (yes_price_cents / Decimal(100))
                                            prices[position_key] = no_price
                            else:
                                # Try as Kalshi ticker (legacy format without side)
                                try:
                                    orderbook_data = await dome.kalshi.orderbooks.get_orderbooks({
                                        "ticker": position_key,
                                        "end_time": dome._clock.current_time * 1000,
                                        "limit": 1
                                    })
                                    if hasattr(orderbook_data, 'snapshots') and orderbook_data.snapshots:
                                        snapshot = orderbook_data.snapshots[0]
                                        # Default to YES price if side not specified
                                        if hasattr(snapshot, 'orderbook'):
                                            ob = snapshot.orderbook
                                        elif isinstance(snapshot, dict):
                                            ob = snapshot.get('orderbook', {})
                                        else:
                                            ob = {}
                                        
                                        no_bids = ob.get('no', []) if isinstance(ob, dict) else []
                                        if no_bids:
                                            no_price_cents = Decimal(str(no_bids[0][0]))
                                            yes_price = Decimal(1) - (no_price_cents / Decimal(100))
                                            prices[position_key] = yes_price
                                except:
                                    pass
                        except:
                            pass
                return prices
            get_prices = auto_get_prices
        
        equity_curve = []
        
        # Check strategy signature - support both (dome) and (dome, portfolio)
        sig = inspect.signature(strategy)
        param_count = len(sig.parameters)
        
        # Calculate total ticks for progress
        total_ticks = ((effective_end_time - self.start_time) // self.step) + 1
        current_tick = 0
        
        from datetime import datetime
        
        while self._clock.current_time <= effective_end_time:
            current_tick += 1
            current_time_str = datetime.fromtimestamp(self._clock.current_time).strftime('%Y-%m-%d %H:%M:%S')
            
            # Show progress if verbose
            if self.verbose:
                prices = await get_prices(self)
                current_value = self._portfolio.get_value(prices)
                print(f"\n[Tick {current_tick}/{total_ticks}] {current_time_str} | "
                      f"Cash: ${self._portfolio.cash:,.2f} | Value: ${current_value:,.2f} | "
                      f"Positions: {len(self._portfolio.positions)}")
            
            # Call on_tick callback if provided
            if self.on_tick:
                await self.on_tick(self, self._portfolio)
            
            # Run strategy with appropriate signature
            if param_count == 1:
                await strategy(self)
            else:
                await strategy(self, self._portfolio)
            
            # Process pending limit orders (GTC/GTD)
            if hasattr(self.polymarket.markets, '_order_manager'):
                if self.polymarket.markets._order_manager:
                    await self.polymarket.markets._order_manager.process_pending_orders("polymarket")
            if hasattr(self.kalshi.markets, '_order_manager'):
                if self.kalshi.markets._order_manager:
                    await self.kalshi.markets._order_manager.process_pending_orders("kalshi")
            
            # Record equity
            prices = await get_prices(self)
            value = self._portfolio.get_value(prices)
            
            # Calculate positions value for interest accrual
            positions_value = sum(
                qty * prices.get(token_id, Decimal(0))
                for token_id, qty in self._portfolio.positions.items()
            )
            
            # Accrue daily interest (Kalshi)
            if self._portfolio.enable_interest and self._portfolio.interest_accrual:
                daily_interest = self._portfolio.interest_accrual.accrue_interest(
                    cash_balance=self._portfolio.cash,
                    positions_value=positions_value,
                    current_timestamp=self._clock.current_time
                )
                if daily_interest > 0:
                    # Add interest to cash (paid monthly, but we accrue daily)
                    # For backtesting, we can add it daily or track separately
                    self._portfolio.cash += daily_interest
            
            equity_curve.append((self._clock.current_time, value))
            
            # Advance time
            self._clock.advance_by(self.step)
        
        # Final valuation
        final_prices = await get_prices(self)
        final_value = self._portfolio.get_value(final_prices)
        
        # Calculate total interest earned
        total_interest = Decimal(0)
        if self._portfolio.interest_accrual:
            total_interest = self._portfolio.interest_accrual.total_interest_paid
        
        return BacktestResult(
            initial_cash=self.initial_cash,
            final_value=final_value,
            equity_curve=equity_curve,
            trades=self._portfolio.trades,
            total_fees_paid=self._portfolio.total_fees_paid,
            total_interest_earned=total_interest,
        )
