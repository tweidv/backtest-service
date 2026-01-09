"""Kalshi orderbooks namespace: dome.kalshi.orderbooks.*"""

from typing import TYPE_CHECKING, Union

from ..base_api import BasePlatformAPI

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ...simulation.clock import SimulationClock
    from ...simulation.portfolio import Portfolio
    from ..rate_limiter import RateLimiter


class KalshiOrderbooksNamespace(BasePlatformAPI):
    """dome.kalshi.orderbooks.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limiter: Union["RateLimiter", float, None] = None
    ):
        super().__init__("kalshi", real_client, clock, portfolio, rate_limiter)
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
        
        response = await self._call_api(self._real_api.orderbooks.get_orderbooks, params)
        
        # CRITICAL: Filter response data to remove orderbook snapshots after backtest time
        # Kalshi orderbooks use 'timestamp' field (in milliseconds)
        if hasattr(response, 'snapshots') and response.snapshots:
            at_time_ms = self._clock.current_time * 1000  # Convert to milliseconds
            filtered_snapshots = []
            for snapshot in response.snapshots:
                # Get timestamp from snapshot (field name: timestamp, in milliseconds)
                snapshot_timestamp = None
                if hasattr(snapshot, 'timestamp'):
                    snapshot_timestamp = snapshot.timestamp
                elif isinstance(snapshot, dict):
                    snapshot_timestamp = snapshot.get('timestamp')
                
                # Only include snapshots that occurred at or before backtest time
                if snapshot_timestamp is not None and snapshot_timestamp <= at_time_ms:
                    filtered_snapshots.append(snapshot)
            
            # Create filtered response
            try:
                import copy
                if hasattr(response, '__dict__'):
                    filtered_response = copy.copy(response)
                    filtered_response.snapshots = filtered_snapshots
                    return filtered_response
            except (AttributeError, TypeError):
                # Fallback if copy fails - create simple response object
                class FilteredResponse:
                    def __init__(self, snapshots, pagination=None):
                        self.snapshots = snapshots
                        self.pagination = pagination
                pagination = getattr(response, 'pagination', None)
                return FilteredResponse(filtered_snapshots, pagination)
        
        return response

