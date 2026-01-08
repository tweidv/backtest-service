"""Implementation functions for Polymarket API - extracted for reuse in namespace structure."""

from decimal import Decimal
from typing import TYPE_CHECKING

from .base_api import BasePlatformAPI
from .models import HistoricalMarket, HistoricalMarketsResponse

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ..simulation.clock import SimulationClock
    from ..simulation.portfolio import Portfolio


async def _get_markets_impl(self: BasePlatformAPI, params: dict = None) -> HistoricalMarketsResponse:
    """Implementation of get_markets - extracted for reuse."""
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
            api_params['limit'] = min(limit, 100)
            
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


async def _get_market_price_impl(self: BasePlatformAPI, params: dict) -> dict:
    """Implementation of get_market_price - extracted for reuse."""
    params['at_time'] = params.get('at_time', self._clock.current_time)
    return await self._call_api(self._real_api.markets.get_market_price, params)


async def _get_candlesticks_impl(self: BasePlatformAPI, params: dict) -> dict:
    """Implementation of get_candlesticks - extracted for reuse."""
    if 'condition_id' not in params:
        raise ValueError("condition_id is required for get_candlesticks")
    
    if 'start_time' not in params or 'end_time' not in params:
        raise ValueError("start_time and end_time are required for get_candlesticks")
    
    self._cap_time_at_backtest(params, 'end_time', is_milliseconds=False)
    
    interval = params.get('interval', 1)
    start_time = params['start_time']
    end_time = params['end_time']
    time_range = end_time - start_time
    
    if interval == 1:
        max_range = 7 * 24 * 3600
        if time_range > max_range:
            raise ValueError(f"For 1m interval, max range is 1 week. Requested range: {time_range / (24 * 3600):.2f} days")
    elif interval == 60:
        max_range = 30 * 24 * 3600
        if time_range > max_range:
            raise ValueError(f"For 1h interval, max range is 1 month. Requested range: {time_range / (24 * 3600):.2f} days")
    elif interval == 1440:
        max_range = 365 * 24 * 3600
        if time_range > max_range:
            raise ValueError(f"For 1d interval, max range is 1 year. Requested range: {time_range / (365 * 24 * 3600):.2f} years")
    
    response = await self._call_api(self._real_api.markets.get_candlesticks, params)
    
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


async def _get_orderbooks_impl(self: BasePlatformAPI, params: dict) -> dict:
    """Implementation of get_orderbooks - extracted for reuse."""
    self._cap_time_at_backtest(params, 'end_time', is_milliseconds=True)
    return await self._call_api(self._real_api.markets.get_orderbooks, params)

