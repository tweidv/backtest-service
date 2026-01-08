"""Kalshi orderbooks namespace: dome.kalshi.orderbooks.*"""

from typing import TYPE_CHECKING

from ..base_api import BasePlatformAPI

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ...simulation.clock import SimulationClock
    from ...simulation.portfolio import Portfolio


class KalshiOrderbooksNamespace(BasePlatformAPI):
    """dome.kalshi.orderbooks.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limit: float = 1.1
    ):
        super().__init__("kalshi", real_client, clock, portfolio, rate_limit)
        self._real_api = real_client.kalshi

    async def get_orderbooks(self, params: dict) -> dict:
        """
        Get Kalshi orderbook history up to backtest time.
        
        Matches: dome.kalshi.orderbooks.get_orderbooks()
        
        Parameters (from Dome docs):
        - ticker: Required - The Kalshi market ticker
        - start_time: Optional - Unix timestamp (milliseconds). If not provided with end_time, returns latest snapshot
        - end_time: Optional - Unix timestamp (milliseconds). If not provided with start_time, returns latest snapshot
        - limit: Optional - Max snapshots to return (default: 100). Ignored when fetching latest.
        
        Note: All timestamps are in milliseconds (not seconds like other endpoints).
        Orderbook data has history starting from October 29th, 2025.
        """
        if 'ticker' not in params:
            raise ValueError("ticker is required for get_orderbooks")
        
        # Cap end_time at backtest time (Kalshi orderbooks use milliseconds)
        self._cap_time_at_backtest(params, 'end_time', is_milliseconds=True)
        
        # Cap start_time if provided
        if 'start_time' in params:
            self._cap_time_at_backtest(params, 'start_time', is_milliseconds=True)
        
        return await self._call_api(self._real_api.orderbooks.get_orderbooks, params)

