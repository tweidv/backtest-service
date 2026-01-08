"""Chainlink crypto prices namespace: dome.crypto_prices.chainlink.*"""

from typing import TYPE_CHECKING

from ..base_api import BasePlatformAPI

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ...simulation.clock import SimulationClock
    from ...simulation.portfolio import Portfolio


class ChainlinkNamespace(BasePlatformAPI):
    """dome.crypto_prices.chainlink.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limit: float = 1.1
    ):
        super().__init__("crypto", real_client, clock, portfolio, rate_limit)
        self._real_api = real_client.crypto_prices

    async def get_chainlink_prices(self, params: dict) -> dict:
        """
        Get historical crypto price data from Chainlink up to backtest time.
        
        Matches: dome.crypto_prices.chainlink.get_chainlink_prices()
        
        Parameters (from Dome docs):
        - currency: Required - Currency pair (slash-separated, e.g., btc/usd, eth/usd)
        - start_time: Optional - Unix timestamp (milliseconds). If not provided with end_time, returns latest price
        - end_time: Optional - Unix timestamp (milliseconds). If not provided with start_time, returns latest price
        - limit: Optional - Maximum number of prices to return (default: 100)
        
        Note: All timestamps are in milliseconds (not seconds).
        Currency format: slash-separated (e.g., btc/usd, eth/usd).
        """
        if 'currency' not in params:
            raise ValueError("currency is required for get_chainlink_prices")
        
        # Validate currency format (slash-separated)
        currency = params.get('currency')
        if '/' not in currency:
            raise ValueError(
                f"currency must be slash-separated. Got: {currency}. Example: btc/usd, eth/usd"
            )
        
        # Cap end_time at backtest time (Chainlink prices use milliseconds)
        self._cap_time_at_backtest(params, 'end_time', is_milliseconds=True)
        
        # Cap start_time if provided
        if 'start_time' in params:
            self._cap_time_at_backtest(params, 'start_time', is_milliseconds=True)
        
        response = await self._call_api(self._real_api.chainlink.get_chainlink_prices, params)
        
        # CRITICAL: Filter response data to remove prices after backtest time
        # Chainlink prices use 'timestamp' field (in milliseconds)
        if hasattr(response, 'prices') and response.prices:
            at_time_ms = self._clock.current_time * 1000  # Convert to milliseconds
            filtered_prices = []
            for price in response.prices:
                # Get timestamp from price (field name: timestamp, in milliseconds)
                price_timestamp = None
                if hasattr(price, 'timestamp'):
                    price_timestamp = price.timestamp
                elif isinstance(price, dict):
                    price_timestamp = price.get('timestamp')
                
                # Only include prices that occurred at or before backtest time
                if price_timestamp is not None and price_timestamp <= at_time_ms:
                    filtered_prices.append(price)
            
            # Create filtered response
            try:
                import copy
                if hasattr(response, '__dict__'):
                    filtered_response = copy.copy(response)
                    filtered_response.prices = filtered_prices
                    return filtered_response
            except:
                class FilteredResponse:
                    def __init__(self, prices, pagination_key=None):
                        self.prices = prices
                        self.pagination_key = pagination_key
                pagination_key = getattr(response, 'pagination_key', None)
                return FilteredResponse(filtered_prices, pagination_key)
        
        return response

