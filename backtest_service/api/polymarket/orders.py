"""Polymarket orders namespace: dome.polymarket.orders.*"""

from typing import TYPE_CHECKING

from ..base_api import BasePlatformAPI

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ...simulation.clock import SimulationClock
    from ...simulation.portfolio import Portfolio


class PolymarketOrdersNamespace(BasePlatformAPI):
    """dome.polymarket.orders.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limit: float = 1.1
    ):
        super().__init__("polymarket", real_client, clock, portfolio, rate_limit)
        self._real_api = real_client.polymarket

    async def get_orders(self, params: dict = None) -> dict:
        """
        Get orders up to backtest time.
        
        Matches: dome.polymarket.orders.get_orders()
        
        Parameters (from Dome docs):
        - market_slug: Optional - Filter by market slug (can be array)
        - condition_id: Optional - Filter by condition ID (can be array)
        - token_id: Optional - Filter by token ID (can be array)
        - user: Optional - Filter by user wallet address
        - start_time: Optional - Unix timestamp (seconds) - filter from this time (inclusive)
        - end_time: Optional - Unix timestamp (seconds) - filter until this time (inclusive)
        - limit: Optional - Number of orders to return (1-1000, default: 100)
        - offset: Optional - Number of orders to skip for pagination (default: 0)
        
        Note: Only one of market_slug, token_id, or condition_id can be provided.
        """
        params = params or {}
        at_time = self._clock.current_time
        
        # Cap end_time at backtest time to prevent lookahead (orders use seconds)
        if 'end_time' in params:
            params['end_time'] = min(params['end_time'], at_time)
        else:
            params['end_time'] = at_time
        
        # Cap start_time if provided
        if 'start_time' in params:
            params['start_time'] = min(params['start_time'], at_time)
        
        return await self._call_api(self._real_api.orders.get_orders, params)

