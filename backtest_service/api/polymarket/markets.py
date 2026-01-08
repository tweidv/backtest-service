"""Polymarket markets namespace: dome.polymarket.markets.*"""

from decimal import Decimal
from typing import TYPE_CHECKING

from ..base_api import BasePlatformAPI
from ..models import HistoricalMarket, HistoricalMarketsResponse

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ...simulation.clock import SimulationClock
    from ...simulation.portfolio import Portfolio


class PolymarketMarketsNamespace(BasePlatformAPI):
    """dome.polymarket.markets.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limit: float = 1.1
    ):
        super().__init__("polymarket", real_client, clock, portfolio, rate_limit)
        self._real_api = real_client.polymarket

    async def get_markets(self, params: dict = None) -> HistoricalMarketsResponse:
        """
        Get markets that existed at the current backtest time.
        
        Matches: dome.polymarket.markets.get_markets()
        
        Parameters (from Dome docs):
        - status: Filter by status (open/closed)
        - limit: Number of markets to return (1-100, default: 10)
        - offset: Number of markets to skip for pagination
        - min_volume: Filter markets with volume >= this amount
        - market_slug: Filter by market slug(s) - can be array
        - tags: Filter by tags - can be array
        - start_time: Unix timestamp (seconds) - filter markets by creation time
        - end_time: Unix timestamp (seconds) - filter markets by creation time
        """
        params = params or {}
        at_time = self._clock.current_time
        
        # Extract and remove status filter - we'll apply it ourselves
        requested_status = params.pop('status', None)
        original_limit = params.get('limit', 100)
        
        # Smart progressive time window expansion
        time_windows = []
        if requested_status == 'open':
            base_window = 7 * 24 * 3600  # 7 days
            time_windows = [
                (at_time - base_window, at_time + base_window * 3),
                (at_time - base_window * 2, at_time + base_window * 6),
                (at_time - base_window * 4, at_time + base_window * 12),
                (at_time - (90 * 24 * 3600), at_time + (180 * 24 * 3600)),
                (at_time - (180 * 24 * 3600), at_time + (365 * 24 * 3600)),
                (at_time - (365 * 24 * 3600), at_time + (365 * 24 * 3600)),
            ]
        elif requested_status == 'closed':
            base_window = 7 * 24 * 3600
            time_windows = [
                (at_time - base_window * 2, at_time),
                (at_time - base_window * 4, at_time),
                (at_time - (90 * 24 * 3600), at_time),
                (at_time - (180 * 24 * 3600), at_time),
                (at_time - (365 * 24 * 3600), at_time),
                (at_time - (365 * 24 * 3600), at_time + (365 * 24 * 3600)),
            ]
        else:
            base_window = 7 * 24 * 3600
            time_windows = [
                (at_time - base_window, at_time + base_window),
                (at_time - base_window * 2, at_time + base_window * 2),
                (at_time - base_window * 4, at_time + base_window * 4),
                (at_time - (90 * 24 * 3600), at_time + (90 * 24 * 3600)),
                (at_time - (180 * 24 * 3600), at_time + (180 * 24 * 3600)),
                (at_time - (365 * 24 * 3600), at_time + (365 * 24 * 3600)),
            ]
        
        seen_market_ids = set()
        filtered_markets = []
        
        for window_start, window_end in time_windows:
            if 'start_time' in params:
                window_start = params['start_time']
            if 'end_time' in params:
                window_end = params['end_time']
            
            api_params = params.copy()
            api_params['start_time'] = window_start
            api_params['end_time'] = window_end
            
            offset = 0
            limit = api_params.get('limit', 100)
            page_count = 0
            max_pages_per_window = 20
            consecutive_empty_pages = 0
            markets_found_in_this_window = 0
            
            while page_count < max_pages_per_window:
                api_params['offset'] = offset
                api_params['limit'] = min(limit, 100)  # API max is 100
                
                response = await self._call_api(self._real_api.markets.get_markets, api_params)
                
                if not response.markets:
                    break
                
                page_count += 1
                new_markets_in_window = 0
                
                for market in response.markets:
                    market_id = getattr(market, 'condition_id', None) or getattr(market, 'market_slug', None)
                    if market_id and market_id in seen_market_ids:
                        continue
                    
                    if not self._market_existed_at_time(market, at_time):
                        continue
                    
                    if requested_status == 'open':
                        if not self._market_was_open_at_time(market, at_time):
                            continue
                    elif requested_status == 'closed':
                        if not self._market_was_closed_at_time(market, at_time):
                            continue
                    
                    filtered_markets.append(market)
                    if market_id:
                        seen_market_ids.add(market_id)
                    new_markets_in_window += 1
                    markets_found_in_this_window += 1
                
                if original_limit and len(filtered_markets) >= original_limit:
                    break
                
                if hasattr(response, 'pagination') and response.pagination:
                    if isinstance(response.pagination, dict):
                        has_more = response.pagination.get('has_more', False)
                    else:
                        has_more = getattr(response.pagination, 'has_more', False)
                    if not has_more:
                        break
                    offset += len(response.markets)
                else:
                    if len(response.markets) < api_params['limit']:
                        break
                    offset += len(response.markets)
                
                if new_markets_in_window == 0:
                    consecutive_empty_pages += 1
                    if (consecutive_empty_pages >= 3 and 
                        page_count >= 5 and 
                        markets_found_in_this_window == 0):
                        break
                else:
                    consecutive_empty_pages = 0
            
            if original_limit and len(filtered_markets) >= original_limit:
                break
            
            if not original_limit and len(filtered_markets) >= 500:
                break
        
        historical_markets = []
        for market in filtered_markets:
            historical_market = HistoricalMarket.from_market(market, at_time)
            historical_markets.append(historical_market)
        
        if original_limit and original_limit < len(historical_markets):
            historical_markets = historical_markets[:original_limit]
        
        return HistoricalMarketsResponse(
            markets=historical_markets,
            total_at_time=len(historical_markets),
            backtest_time=at_time,
        )

    async def get_market_price(self, params: dict) -> dict:
        """
        Get market price at backtest time.
        
        Matches: dome.polymarket.markets.get_market_price()
        
        Parameters (from Dome docs):
        - token_id: Required - The token ID for the Polymarket market (path parameter in API, but SDK handles it)
        - at_time: Optional - Unix timestamp (seconds) for historical price lookup
        """
        # SDK handles token_id as path parameter, we pass it in params
        if 'token_id' not in params:
            raise ValueError("token_id is required for get_market_price")
        
        # Set at_time to backtest time if not provided
        params['at_time'] = params.get('at_time', self._clock.current_time)
        
        # Cap at_time at backtest time to prevent lookahead
        params['at_time'] = min(params['at_time'], self._clock.current_time)
        
        return await self._call_api(self._real_api.markets.get_market_price, params)

    async def get_candlesticks(self, params: dict) -> dict:
        """
        Get candlestick data up to backtest time.
        
        Matches: dome.polymarket.markets.get_candlesticks()
        
        Parameters (from Dome docs):
        - condition_id: Required - The condition ID for the market (path parameter)
        - start_time: Required - Unix timestamp (seconds) for start of time range
        - end_time: Required - Unix timestamp (seconds) for end of time range
        - interval: Optional - 1 (1m), 60 (1h), or 1440 (1d). Defaults to 1.
          Range limits: 1m (max 1 week), 1h (max 1 month), 1d (max 1 year)
        """
        if 'condition_id' not in params:
            raise ValueError("condition_id is required for get_candlesticks")
        
        if 'start_time' not in params or 'end_time' not in params:
            raise ValueError("start_time and end_time are required for get_candlesticks")
        
        # Cap end_time at backtest time (candlesticks use seconds)
        self._cap_time_at_backtest(params, 'end_time', is_milliseconds=False)
        
        interval = params.get('interval', 1)
        start_time = params['start_time']
        end_time = params['end_time']
        time_range = end_time - start_time
        
        # Validate range limits per Dome docs
        if interval == 1:  # 1 minute
            max_range = 7 * 24 * 3600  # 1 week
            if time_range > max_range:
                raise ValueError(
                    f"For 1m interval, max range is 1 week. "
                    f"Requested range: {time_range / (24 * 3600):.2f} days"
                )
        elif interval == 60:  # 1 hour
            max_range = 30 * 24 * 3600  # 1 month
            if time_range > max_range:
                raise ValueError(
                    f"For 1h interval, max range is 1 month. "
                    f"Requested range: {time_range / (24 * 3600):.2f} days"
                )
        elif interval == 1440:  # 1 day
            max_range = 365 * 24 * 3600  # 1 year
            if time_range > max_range:
                raise ValueError(
                    f"For 1d interval, max range is 1 year. "
                    f"Requested range: {time_range / (365 * 24 * 3600):.2f} years"
                )
        
        response = await self._call_api(self._real_api.markets.get_candlesticks, params)
        
        # Filter candlesticks to only include those up to backtest time
        if hasattr(response, 'candlesticks') and response.candlesticks:
            filtered_candlesticks = []
            at_time = self._clock.current_time
            
            for candlestick_tuple in response.candlesticks:
                if not isinstance(candlestick_tuple, (list, tuple)) or len(candlestick_tuple) < 2:
                    continue
                
                candlestick_data = candlestick_tuple[0]
                end_period = None
                if hasattr(candlestick_data, 'end_period_ts'):
                    end_period = candlestick_data.end_period_ts
                elif isinstance(candlestick_data, dict):
                    end_period = candlestick_data.get('end_period_ts')
                
                if end_period is not None and end_period <= at_time:
                    filtered_candlesticks.append(candlestick_tuple)
            
            try:
                import copy
                if hasattr(response, '__dict__'):
                    filtered_response = copy.copy(response)
                    filtered_response.candlesticks = filtered_candlesticks
                    return filtered_response
            except:
                class FilteredResponse:
                    def __init__(self, candlesticks):
                        self.candlesticks = candlesticks
                return FilteredResponse(filtered_candlesticks)
        
        return response

    async def get_orderbooks(self, params: dict) -> dict:
        """
        Get orderbook history up to backtest time.
        
        Matches: dome.polymarket.markets.get_orderbooks()
        
        Parameters (from Dome docs):
        - token_id: Required - The token ID for the Polymarket market
        - start_time: Optional - Unix timestamp (milliseconds). If not provided with end_time, returns latest snapshot
        - end_time: Optional - Unix timestamp (milliseconds). If not provided with start_time, returns latest snapshot
        - limit: Optional - Max snapshots to return (default: 100, max: 200). Ignored when fetching latest.
        - pagination_key: Optional - Pagination key for next chunk. Ignored when fetching latest.
        
        Note: All timestamps are in milliseconds (not seconds like other endpoints).
        Orderbook data has history starting from October 14th, 2025.
        """
        if 'token_id' not in params:
            raise ValueError("token_id is required for get_orderbooks")
        
        # Cap end_time at backtest time (orderbooks use milliseconds)
        self._cap_time_at_backtest(params, 'end_time', is_milliseconds=True)
        
        # Cap start_time if provided
        if 'start_time' in params:
            self._cap_time_at_backtest(params, 'start_time', is_milliseconds=True)
        
        return await self._call_api(self._real_api.markets.get_orderbooks, params)

    def buy(self, token_id: str, quantity: Decimal, price: Decimal):
        """
        Simulate buying tokens (backtest only - convenience method).
        
        Note: Dome doesn't have trading methods (data API only).
        This is a convenience wrapper around portfolio.buy().
        """
        self._portfolio.buy(
            platform=self.platform,
            token_id=token_id,
            quantity=Decimal(quantity),
            price=Decimal(price),
            timestamp=self._clock.current_time,
        )

    def sell(self, token_id: str, quantity: Decimal, price: Decimal):
        """
        Simulate selling tokens (backtest only - convenience method).
        
        Note: Dome doesn't have trading methods (data API only).
        This is a convenience wrapper around portfolio.sell().
        """
        self._portfolio.sell(
            platform=self.platform,
            token_id=token_id,
            quantity=Decimal(quantity),
            price=Decimal(price),
            timestamp=self._clock.current_time,
        )

