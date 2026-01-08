"""Main backtest client that replays historical data."""

from decimal import Decimal
from typing import Callable, Optional

from dome_api_sdk import DomeClient

from ..simulation.clock import SimulationClock
from ..simulation.portfolio import Portfolio
from .polymarket_namespaces import PolymarketNamespace
from .kalshi_namespaces import KalshiNamespace


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
            if not self.api_key:
                raise ValueError("api_key is required in config")
            
            self.start_time = config.get("start_time") or config.get("startTime")
            self.end_time = config.get("end_time") or config.get("endTime")
            if self.start_time is None or self.end_time is None:
                raise ValueError("start_time and end_time are required in config")
            
            self.step = config.get("step", 3600)
            self.initial_cash = Decimal(str(config.get("initial_cash", config.get("initialCash", 10000))))
            
            # Create internal components
            self._clock = SimulationClock(self.start_time)
            self._portfolio = Portfolio(self.initial_cash)
        else:
            # Old style: api_key, clock, portfolio (for backward compatibility)
            if clock is None or portfolio is None:
                raise ValueError("For old-style initialization, clock and portfolio are required")
            self.api_key = config_or_api_key
            self._clock = clock
            self._portfolio = portfolio
            self.start_time = clock.current_time
            self.end_time = None  # Will be set by run() or BacktestRunner
            self.step = 3600
            self.initial_cash = portfolio.cash
        
        self._real_client = DomeClient({"api_key": self.api_key})
        
        # Expose portfolio for strategy access
        self.portfolio = self._portfolio
        
        # Setup platform APIs - matches Dome's nested structure exactly
        self.polymarket = PolymarketNamespace(self._real_client, self._clock, self._portfolio)
        self.kalshi = KalshiNamespace(self._real_client, self._clock, self._portfolio)
    
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
        self._portfolio = Portfolio(self.initial_cash)
        self.portfolio = self._portfolio  # Update reference
        self.polymarket = PolymarketNamespace(self._real_client, self._clock, self._portfolio)
        self.kalshi = KalshiNamespace(self._real_client, self._clock, self._portfolio)
        
        # Auto-detect get_prices if not provided
        if get_prices is None:
            async def auto_get_prices(dome):
                """Auto-detect prices for all positions in portfolio"""
                prices = {}
                for token_id in dome.portfolio.positions.keys():
                    try:
                        # Try polymarket first
                        data = await dome.polymarket.markets.get_market_price({"token_id": token_id})
                        prices[token_id] = Decimal(str(data.price))
                    except:
                        try:
                            # Try kalshi - need to get orderbook and extract price
                            # For now, skip kalshi auto-detection (would need ticker lookup)
                            pass
                        except:
                            pass
                return prices
            get_prices = auto_get_prices
        
        equity_curve = []
        
        # Check strategy signature - support both (dome) and (dome, portfolio)
        sig = inspect.signature(strategy)
        param_count = len(sig.parameters)
        
        while self._clock.current_time <= effective_end_time:
            # Run strategy with appropriate signature
            if param_count == 1:
                await strategy(self)
            else:
                await strategy(self, self._portfolio)
            
            # Record equity
            prices = await get_prices(self)
            value = self._portfolio.get_value(prices)
            equity_curve.append((self._clock.current_time, value))
            
            # Advance time
            self._clock.advance_by(self.step)
        
        # Final valuation
        final_prices = await get_prices(self)
        final_value = self._portfolio.get_value(final_prices)
        
        return BacktestResult(
            initial_cash=self.initial_cash,
            final_value=final_value,
            equity_curve=equity_curve,
            trades=self._portfolio.trades,
        )
