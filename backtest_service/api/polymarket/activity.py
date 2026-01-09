"""Polymarket activity namespace: dome.polymarket.activity.*"""

from typing import TYPE_CHECKING, Union

from ..base_api import BasePlatformAPI

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ...simulation.clock import SimulationClock
    from ...simulation.portfolio import Portfolio
    from ..rate_limiter import RateLimiter


class PolymarketActivityNamespace(BasePlatformAPI):
    """dome.polymarket.activity.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limiter: Union["RateLimiter", float, None] = None
    ):
        super().__init__("polymarket", real_client, clock, portfolio, rate_limiter)
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
        
        response = await self._call_api(self._real_api.activity.get_activity, params)
        
        # CRITICAL: Filter response data to remove activities after backtest time
        # Activity uses 'timestamp' field (in seconds)
        if hasattr(response, 'activities') and response.activities:
            filtered_activities = []
            for activity in response.activities:
                # Get timestamp from activity (field name: timestamp, in seconds)
                activity_timestamp = None
                if hasattr(activity, 'timestamp'):
                    activity_timestamp = activity.timestamp
                elif isinstance(activity, dict):
                    activity_timestamp = activity.get('timestamp')
                
                # Only include activities that occurred at or before backtest time
                if activity_timestamp is not None and activity_timestamp <= at_time:
                    filtered_activities.append(activity)
            
            # Create filtered response
            try:
                import copy
                if hasattr(response, '__dict__'):
                    filtered_response = copy.copy(response)
                    filtered_response.activities = filtered_activities
                    return filtered_response
            except (AttributeError, TypeError):
                # Fallback if copy fails - create simple response object
                class FilteredResponse:
                    def __init__(self, activities, pagination=None):
                        self.activities = activities
                        self.pagination = pagination
                pagination = getattr(response, 'pagination', None)
                return FilteredResponse(filtered_activities, pagination)
        
        return response

