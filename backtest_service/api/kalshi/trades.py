"""Kalshi trades namespace: dome.kalshi.trades.*"""

from typing import TYPE_CHECKING

from ..base_api import BasePlatformAPI

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ...simulation.clock import SimulationClock
    from ...simulation.portfolio import Portfolio


class KalshiTradesNamespace(BasePlatformAPI):
    """dome.kalshi.trades.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limit: float = 1.1
    ):
        super().__init__("kalshi", real_client, clock, portfolio, rate_limit)
        self._real_api = real_client.kalshi

    async def get_trades(self, params: dict = None) -> dict:
        """
        Get Kalshi trade history up to backtest time.
        
        Matches: dome.kalshi.trades.get_trades()
        
        Parameters (from Dome docs):
        - ticker: Optional - The Kalshi market ticker to filter trades
        - start_time: Optional - Unix timestamp (seconds) - filter from this time
        - end_time: Optional - Unix timestamp (seconds) - filter until this time
        - limit: Optional - Maximum number of trades to return (default: 100)
        - offset: Optional - Number of trades to skip for pagination (default: 0)
        
        Note: All timestamps are in seconds.
        Returns executed trades with pricing, volume, and taker side information.
        """
        params = params or {}
        at_time = self._clock.current_time
        
        # Cap end_time at backtest time (Kalshi trades use seconds)
        if 'end_time' in params:
            params['end_time'] = min(params['end_time'], at_time)
        else:
            params['end_time'] = at_time
        
        # Cap start_time if provided
        if 'start_time' in params:
            params['start_time'] = min(params['start_time'], at_time)
        
        return await self._call_api(self._real_api.trades.get_trades, params)

