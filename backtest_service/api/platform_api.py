"""Polymarket platform API wrapper with historical filtering."""

from decimal import Decimal
from typing import TYPE_CHECKING

from .base_api import BasePlatformAPI
from .models import HistoricalMarket, HistoricalMarketsResponse

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ..simulation.clock import SimulationClock
    from ..simulation.portfolio import Portfolio


class PolymarketAPI(BasePlatformAPI):
    """Wraps Polymarket API, injecting at_time from clock.
    
    Note: This is our internal class name. Dome's SDK uses dome.polymarket.markets.*,
    but we flatten it to dome.polymarket.* for convenience.
    """
    
    def __init__(
        self,
        platform: str,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limit: float = 1.1
    ):
        super().__init__(platform, real_client, clock, portfolio, rate_limit)
        self._real_api = getattr(real_client, platform)

    async def get_markets(self, params: dict = None) -> HistoricalMarketsResponse:
        """
        Get markets that existed at the current backtest time.
        
        This emulates calling dome.polymarket.markets.get_markets() but filters
        results to only show markets that would have been visible at clock.current_time.
        
        Key behaviors:
        - Markets with start_time > clock.current_time are excluded (didn't exist yet)
        - If params['status'] == 'open': only markets that were OPEN at backtest time
        - If params['status'] == 'closed': only markets that were CLOSED at backtest time
        - winning_side is hidden if market wasn't resolved yet at backtest time
        - Uses API start_time and end_time parameters to fetch historical markets
        - Handles pagination to get all markets in the time window
        
        Args:
            params: Same params as dome API (tags, min_volume, limit, offset, status, etc.)
                   The 'status' param is intercepted and applied historically.
                   'start_time' and 'end_time' can be provided to override defaults.
        
        Returns:
            HistoricalMarketsResponse with filtered markets and metadata
        """
        params = params or {}
        at_time = self._clock.current_time
        
        # Extract and remove status filter - we'll apply it ourselves
        requested_status = params.pop('status', None)
        
        original_limit = params.get('limit', 100)
        
        # Smart progressive time window expansion
        # Start with smaller windows and expand only if needed
        # This avoids fetching thousands of irrelevant markets
        # Optimized: Start with 7 days (more likely to find results quickly)
        time_windows = []
        if requested_status == 'open':
            # For open markets, we want markets that:
            # - Started before backtest time (start_time <= at_time)
            # - Haven't closed yet (close_time is None OR close_time > at_time)
            # Strategy: Start with very recent markets (7 days) - most likely to be open
            # Then expand by 2x each time for efficient search
            base_window = 7 * 24 * 3600  # 7 days
            time_windows = [
                (at_time - base_window, at_time + base_window * 3),           # 7 days before, 21 days after
                (at_time - base_window * 2, at_time + base_window * 6),      # 14 days before, 42 days after
                (at_time - base_window * 4, at_time + base_window * 12),     # 28 days before, 84 days after
                (at_time - (90 * 24 * 3600), at_time + (180 * 24 * 3600)),  # 90 days before, 180 days after
                (at_time - (180 * 24 * 3600), at_time + (365 * 24 * 3600)), # 180 days before, 1 year after
                (at_time - (365 * 24 * 3600), at_time + (365 * 24 * 3600)), # 1 year before, 1 year after (full range)
            ]
        elif requested_status == 'closed':
            # For closed markets, we want markets that:
            # - Started before backtest time (start_time <= at_time)
            # - Already closed (close_time <= at_time)
            # Strategy: Start with older markets (more likely to be closed)
            # Use smaller initial window since closed markets are more common
            base_window = 7 * 24 * 3600  # 7 days
            time_windows = [
                (at_time - base_window * 2, at_time),                        # 14 days before, up to backtest
                (at_time - base_window * 4, at_time),                        # 28 days before, up to backtest
                (at_time - (90 * 24 * 3600), at_time),                       # 90 days before, up to backtest
                (at_time - (180 * 24 * 3600), at_time),                      # 180 days before, up to backtest
                (at_time - (365 * 24 * 3600), at_time),                      # 1 year before, up to backtest
                (at_time - (365 * 24 * 3600), at_time + (365 * 24 * 3600)),  # Full range as fallback
            ]
        else:
            # No status filter - use balanced approach with smaller initial window
            base_window = 7 * 24 * 3600  # 7 days
            time_windows = [
                (at_time - base_window, at_time + base_window),              # 7 days before/after
                (at_time - base_window * 2, at_time + base_window * 2),      # 14 days before/after
                (at_time - base_window * 4, at_time + base_window * 4),      # 28 days before/after
                (at_time - (90 * 24 * 3600), at_time + (90 * 24 * 3600)),   # 90 days before/after
                (at_time - (180 * 24 * 3600), at_time + (180 * 24 * 3600)), # 180 days before/after
                (at_time - (365 * 24 * 3600), at_time + (365 * 24 * 3600)), # 1 year before/after (full range)
            ]
        
        # Track markets we've already seen to avoid duplicates
        seen_market_ids = set()  # Use condition_id as unique identifier
        filtered_markets = []  # Markets that pass historical filter
        
        # Try each time window progressively
        for window_start, window_end in time_windows:
            # Check if user provided custom time range
            if 'start_time' in params:
                window_start = params['start_time']
            if 'end_time' in params:
                window_end = params['end_time']
            
            api_params = params.copy()
            api_params['start_time'] = window_start
            api_params['end_time'] = window_end
            
            # Reset pagination for this window
            offset = 0
            limit = api_params.get('limit', 100)
            page_count = 0
            max_pages_per_window = 20  # Limit pages per window to avoid getting stuck
            consecutive_empty_pages = 0  # Track empty pages for early exit
            markets_found_in_this_window = 0  # Track how many we found in this specific window
            
            # Fetch markets in this time window
            while page_count < max_pages_per_window:
                api_params['offset'] = offset
                api_params['limit'] = min(limit, 100)  # API max is 100
                
                response = await self._call_api(self._real_api.markets.get_markets, api_params)
                
                if not response.markets:
                    break
                
                page_count += 1
                new_markets_in_window = 0
                
                # Filter markets as we go
                for market in response.markets:
                    # Skip if we've already seen this market (from previous window)
                    market_id = getattr(market, 'condition_id', None) or getattr(market, 'market_slug', None)
                    if market_id and market_id in seen_market_ids:
                        continue
                    
                    # Must have existed at backtest time
                    if not self._market_existed_at_time(market, at_time):
                        continue
                    
                    # Apply historical status filter if requested
                    if requested_status == 'open':
                        if not self._market_was_open_at_time(market, at_time):
                            continue
                    elif requested_status == 'closed':
                        if not self._market_was_closed_at_time(market, at_time):
                            continue
                    
                    # This market passes the filter
                    filtered_markets.append(market)
                    if market_id:
                        seen_market_ids.add(market_id)
                    new_markets_in_window += 1
                    markets_found_in_this_window += 1
                
                # If we have enough filtered markets, we can stop
                if original_limit and len(filtered_markets) >= original_limit:
                    # We have enough! No need to expand to larger windows
                    break
                
                # Check pagination
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
                
                # Safer early exit: only exit if we've checked enough AND haven't found any markets
                # This prevents missing sparse markets
                if new_markets_in_window == 0:
                    consecutive_empty_pages += 1
                    # Only exit early if:
                    # 1. We've checked at least 5 pages (500+ markets checked), AND
                    # 2. We've had 3 consecutive empty pages, AND
                    # 3. We haven't found ANY markets in this window yet (if we found some, keep going - they might be sparse)
                    if (consecutive_empty_pages >= 3 and 
                        page_count >= 5 and 
                        markets_found_in_this_window == 0):
                        # We've checked 500+ markets with no results, and haven't found any in this window
                        # Safe to assume this window is empty and try next window
                        break
                else:
                    consecutive_empty_pages = 0  # Reset counter when we find markets
            
            # If we have enough markets, stop trying larger windows
            if original_limit and len(filtered_markets) >= original_limit:
                break
            
            # If no limit and we got a reasonable amount, we can stop
            if not original_limit and len(filtered_markets) >= 500:
                break
        
        # Convert filtered markets to HistoricalMarket objects
        # (We already filtered during pagination, so filtered_markets contains the right ones)
        historical_markets = []
        
        for market in filtered_markets:
            # Convert to HistoricalMarket with proper historical context
            historical_market = HistoricalMarket.from_market(market, at_time)
            historical_markets.append(historical_market)
        
        # Apply original limit if specified (after filtering)
        if original_limit and original_limit < len(historical_markets):
            historical_markets = historical_markets[:original_limit]
        
        return HistoricalMarketsResponse(
            markets=historical_markets,
            total_at_time=len(historical_markets),
            backtest_time=at_time,
        )

    async def get_market(self, params: dict):
        """Get a single market by slug or other identifier."""
        params['at_time'] = params.get('at_time', self._clock.current_time)
        return await self._call_api(self._real_api.markets.get_market, params)

    async def get_market_price(self, params: dict):
        """Get current or historical market price by token_id."""
        params['at_time'] = params.get('at_time', self._clock.current_time)
        return await self._call_api(self._real_api.markets.get_market_price, params)

    async def get_orderbook_history(self, params: dict):
        """Get historical orderbook snapshots."""
        # Cap end_time at backtest time (orderbooks use milliseconds)
        self._cap_time_at_backtest(params, 'end_time', is_milliseconds=True)
        return await self._call_api(self._real_api.markets.get_orderbooks, params)

    async def get_trade_history(self, params: dict):
        """Get historical trade data (orders)."""
        # Cap end_time at backtest time
        self._cap_time_at_backtest(params, 'end_time', is_milliseconds=False)
        # Try orders.get_orders first (newer SDK), fallback to markets.get_trade_history (older)
        if hasattr(self._real_api, 'orders') and hasattr(self._real_api.orders, 'get_orders'):
            return await self._call_api(self._real_api.orders.get_orders, params)
        else:
            return await self._call_api(self._real_api.markets.get_trade_history, params)

    async def get_candlesticks(self, params: dict):
        """
        Get historical candlestick data for a market.
        
        Args:
            params: Must include:
                - condition_id: The condition ID for the market (required)
                - start_time: Unix timestamp in seconds (required)
                - end_time: Unix timestamp in seconds (required)
                - interval: 1 (1m), 60 (1h), or 1440 (1d). Defaults to 1.
        
        Returns:
            Candlestick data with historical filtering applied.
            
        Note:
            - Interval range limits: 1m (max 1 week), 1h (max 1 month), 1d (max 1 year)
            - end_time is automatically capped at clock.current_time
            - Only candlesticks up to backtest time are returned
        """
        if 'condition_id' not in params:
            raise ValueError("condition_id is required for get_candlesticks")
        
        if 'start_time' not in params or 'end_time' not in params:
            raise ValueError("start_time and end_time are required for get_candlesticks")
        
        # Cap end_time at backtest time (candlesticks use seconds)
        self._cap_time_at_backtest(params, 'end_time', is_milliseconds=False)
        
        # Validate interval range limits
        interval = params.get('interval', 1)
        start_time = params['start_time']
        end_time = params['end_time']
        time_range = end_time - start_time
        
        # Check range limits based on interval
        if interval == 1:  # 1 minute
            max_range = 7 * 24 * 3600  # 1 week in seconds
            if time_range > max_range:
                raise ValueError(
                    f"For 1m interval, max range is 1 week. "
                    f"Requested range: {time_range / (24 * 3600):.2f} days"
                )
        elif interval == 60:  # 1 hour
            max_range = 30 * 24 * 3600  # 1 month in seconds
            if time_range > max_range:
                raise ValueError(
                    f"For 1h interval, max range is 1 month. "
                    f"Requested range: {time_range / (24 * 3600):.2f} days"
                )
        elif interval == 1440:  # 1 day
            max_range = 365 * 24 * 3600  # 1 year in seconds
            if time_range > max_range:
                raise ValueError(
                    f"For 1d interval, max range is 1 year. "
                    f"Requested range: {time_range / (365 * 24 * 3600):.2f} years"
                )
        
        # Call the API
        response = await self._call_api(self._real_api.markets.get_candlesticks, params)
        
        # Filter candlesticks to only include those up to backtest time
        # The response structure is: { candlesticks: [[candlestick_data, token_metadata], ...] }
        if hasattr(response, 'candlesticks') and response.candlesticks:
            filtered_candlesticks = []
            at_time = self._clock.current_time
            
            for candlestick_tuple in response.candlesticks:
                if not isinstance(candlestick_tuple, (list, tuple)) or len(candlestick_tuple) < 2:
                    continue
                
                candlestick_data = candlestick_tuple[0]
                
                # Extract end_period_ts from candlestick data
                end_period = None
                if hasattr(candlestick_data, 'end_period_ts'):
                    end_period = candlestick_data.end_period_ts
                elif isinstance(candlestick_data, dict):
                    end_period = candlestick_data.get('end_period_ts')
                
                # Only include candlesticks that ended before or at backtest time
                if end_period is not None and end_period <= at_time:
                    filtered_candlesticks.append(candlestick_tuple)
                # If we can't determine timestamp, exclude it to be safe (no future data)
            
            # Create a new response object with filtered data
            # Try to preserve the original response structure
            try:
                import copy
                if hasattr(response, '__dict__'):
                    filtered_response = copy.copy(response)
                    filtered_response.candlesticks = filtered_candlesticks
                    return filtered_response
            except:
                # Fallback: return a simple object with candlesticks
                class FilteredResponse:
                    def __init__(self, candlesticks):
                        self.candlesticks = candlesticks
                return FilteredResponse(filtered_candlesticks)
        
        return response

    # Simulated order methods - execute against portfolio
    def buy(self, token_id: str, quantity: Decimal, price: Decimal):
        """Place a buy order (simulated, executes against portfolio)."""
        self._portfolio.buy(
            platform=self.platform,
            token_id=token_id,
            quantity=Decimal(quantity),
            price=Decimal(price),
            timestamp=self._clock.current_time,
        )

    def sell(self, token_id: str, quantity: Decimal, price: Decimal):
        """Place a sell order (simulated, executes against portfolio)."""
        self._portfolio.sell(
            platform=self.platform,
            token_id=token_id,
            quantity=Decimal(quantity),
            price=Decimal(price),
            timestamp=self._clock.current_time,
        )

