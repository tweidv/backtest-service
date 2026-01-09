"""Kalshi trades namespace: dome.kalshi.trades.*"""

from typing import TYPE_CHECKING, Union

from ..base_api import BasePlatformAPI

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ...simulation.clock import SimulationClock
    from ...simulation.portfolio import Portfolio
    from ..rate_limiter import RateLimiter


class KalshiTradesNamespace(BasePlatformAPI):
    """dome.kalshi.trades.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limiter: Union["RateLimiter", float, None] = None
    ):
        super().__init__("kalshi", real_client, clock, portfolio, rate_limiter)
        self._real_api = real_client.kalshi
        # Check if trades namespace exists (may not be in SDK yet)
        # If not, we'll need to call the API directly via HTTP
        self._trades_available = hasattr(self._real_api, 'trades')

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
        
        # Check if trades namespace exists in SDK
        if not self._trades_available:
            # SDK doesn't have trades yet - call API directly
            # This is a workaround until SDK is updated
            import aiohttp
            import os
            
            api_key = os.environ.get('DOME_API_KEY', '')
            if not api_key:
                # Try to get from real_client if possible
                if hasattr(self._real_client, '_api_key'):
                    api_key = self._real_client._api_key
                elif hasattr(self._real_client, 'api_key'):
                    api_key = self._real_client.api_key
                else:
                    raise ValueError("API key required for Kalshi trades (SDK doesn't support this endpoint yet)")
            
            url = "https://api.domeapi.io/v1/kalshi/trades"
            headers = {"Authorization": f"Bearer {api_key}"}
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers, params=params) as resp:
                    if resp.status != 200:
                        error_text = await resp.text()
                        raise ValueError(f"Request failed: {resp.status} {error_text}")
                    response_data = await resp.json()
                    # Convert to object-like response for consistency
                    class Response:
                        def __init__(self, data):
                            self.trades = data.get('trades', [])
                            self.pagination = data.get('pagination', {})
                    response = Response(response_data)
        else:
            response = await self._call_api(self._real_api.trades.get_trades, params)
        
        # CRITICAL: Filter response data to remove trades after backtest time
        # Kalshi trades use 'created_time' field (in seconds)
        if hasattr(response, 'trades') and response.trades:
            filtered_trades = []
            for trade in response.trades:
                # Get timestamp from trade (field name: created_time, in seconds)
                trade_timestamp = None
                if hasattr(trade, 'created_time'):
                    trade_timestamp = trade.created_time
                elif isinstance(trade, dict):
                    trade_timestamp = trade.get('created_time')
                
                # Only include trades that occurred at or before backtest time
                if trade_timestamp is not None and trade_timestamp <= at_time:
                    filtered_trades.append(trade)
            
            # Create filtered response
            try:
                import copy
                if hasattr(response, '__dict__'):
                    filtered_response = copy.copy(response)
                    filtered_response.trades = filtered_trades
                    return filtered_response
            except:
                class FilteredResponse:
                    def __init__(self, trades, pagination=None):
                        self.trades = trades
                        self.pagination = pagination
                pagination = getattr(response, 'pagination', None)
                return FilteredResponse(filtered_trades, pagination)
        
        return response

