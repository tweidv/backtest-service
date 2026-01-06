from decimal import Decimal
from typing import Callable, Dict, TYPE_CHECKING

from ..models.result import BacktestResult
from .clock import SimulationClock
from .portfolio import Portfolio

if TYPE_CHECKING:
    from ..api.client import DomeBacktestClient


class BacktestRunner:
    def __init__(
        self,
        api_key: str,
        start_time: int,
        end_time: int,
        step: int = 3600,  # 1 hour default
        initial_cash: Decimal = Decimal(10000),
    ):
        self.api_key = api_key
        self.start_time = start_time
        self.end_time = end_time
        self.step = step
        self.initial_cash = Decimal(initial_cash)

    async def run(
        self,
        strategy: Callable,
        get_prices: Callable[["DomeBacktestClient"], Dict[str, Decimal]],
    ) -> BacktestResult:
        """
        Run backtest.
        
        Args:
            strategy: async fn(dome, portfolio) called each tick
            get_prices: fn(dome) -> {token_id: price} for valuing positions
        """
        # Import here to avoid circular import
        from ..api.client import DomeBacktestClient
        
        clock = SimulationClock(self.start_time)
        portfolio = Portfolio(self.initial_cash)
        dome = DomeBacktestClient(self.api_key, clock, portfolio)
        
        equity_curve = []

        while clock.current_time <= self.end_time:
            # Run strategy
            await strategy(dome, portfolio)
            
            # Record equity
            prices = await get_prices(dome)
            value = portfolio.get_value(prices)
            equity_curve.append((clock.current_time, value))
            
            # Advance time
            clock.advance_by(self.step)

        # Final valuation
        final_prices = await get_prices(dome)
        final_value = portfolio.get_value(final_prices)

        return BacktestResult(
            initial_cash=self.initial_cash,
            final_value=final_value,
            equity_curve=equity_curve,
            trades=portfolio.trades,
        )

