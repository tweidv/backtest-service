"""Polymarket activity namespace: dome.polymarket.activity.*"""

from typing import TYPE_CHECKING

from ..base_api import BasePlatformAPI

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ...simulation.clock import SimulationClock
    from ...simulation.portfolio import Portfolio


class PolymarketActivityNamespace(BasePlatformAPI):
    """dome.polymarket.activity.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limit: float = 1.1
    ):
        super().__init__("polymarket", real_client, clock, portfolio, rate_limit)
        self._real_api = real_client.polymarket

    async def get_activity(self, params: dict = None) -> dict:
        """
        Get activity up to backtest time.
        
        Matches: dome.polymarket.activity.get_activity()
        
        Parameters (from Dome docs):
        - user: Required - User wallet address to fetch activity for
        - start_time: Optional - Unix timestamp (seconds) - filter from this time (inclusive)
        - end_time: Optional - Unix timestamp (seconds) - filter until this time (inclusive)
        - market_slug: Optional - Filter by market slug
        - condition_id: Optional - Filter by condition ID
        - limit: Optional - Number of activities to return (1-1000, default: 100)
        - offset: Optional - Number of activities to skip for pagination (default: 0)
        
        Returns: Trading activity including MERGES, SPLITS, and REDEEMS
        """
        params = params or {}
        
        if 'user' not in params:
            raise ValueError("user (wallet address) is required for get_activity")
        
        at_time = self._clock.current_time
        
        # Cap end_time at backtest time (activity uses seconds)
        if 'end_time' in params:
            params['end_time'] = min(params['end_time'], at_time)
        else:
            params['end_time'] = at_time
        
        # Cap start_time if provided
        if 'start_time' in params:
            params['start_time'] = min(params['start_time'], at_time)
        
        return await self._call_api(self._real_api.activity.get_activity, params)

