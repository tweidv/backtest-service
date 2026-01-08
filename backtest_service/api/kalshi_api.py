"""Kalshi platform API wrapper with historical filtering."""

from decimal import Decimal
from typing import TYPE_CHECKING

from .base_api import BasePlatformAPI
from .models import HistoricalKalshiMarket, HistoricalKalshiMarketsResponse

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ..simulation.clock import SimulationClock
    from ..simulation.portfolio import Portfolio


class KalshiAPI(BasePlatformAPI):
    """Wraps Kalshi API with historical filtering for backtesting."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limit: float = 1.1
    ):
        super().__init__("kalshi", real_client, clock, portfolio, rate_limit)
        self._real_api = real_client.kalshi

    async def get_markets(self, params: dict = None) -> HistoricalKalshiMarketsResponse:
        """
        Get Kalshi markets that existed at the current backtest time.
        
        Same historical filtering logic as Polymarket get_markets.
        Uses API start_time and end_time parameters to fetch historical markets.
        """
        params = params or {}
        at_time = self._clock.current_time
        
        requested_status = params.pop('status', None)
        original_limit = params.get('limit', 100)
        
        # Smart progressive time window expansion (same optimized strategy as Polymarket)
        # Start with 7 days for faster results
        time_windows = []
        base_window = 7 * 24 * 3600  # 7 days
        if requested_status == 'open':
            time_windows = [
                (at_time - base_window, at_time + base_window * 3),           # 7 days before, 21 days after
                (at_time - base_window * 2, at_time + base_window * 6),       # 14 days before, 42 days after
                (at_time - base_window * 4, at_time + base_window * 12),     # 28 days before, 84 days after
                (at_time - (90 * 24 * 3600), at_time + (180 * 24 * 3600)),   # 90 days before, 180 days after
                (at_time - (180 * 24 * 3600), at_time + (365 * 24 * 3600)),  # 180 days before, 1 year after
                (at_time - (365 * 24 * 3600), at_time + (365 * 24 * 3600)),  # Full range
            ]
        elif requested_status == 'closed':
            time_windows = [
                (at_time - base_window * 2, at_time),                         # 14 days before, up to backtest
                (at_time - base_window * 4, at_time),                         # 28 days before, up to backtest
                (at_time - (90 * 24 * 3600), at_time),                       # 90 days before, up to backtest
                (at_time - (180 * 24 * 3600), at_time),                       # 180 days before, up to backtest
                (at_time - (365 * 24 * 3600), at_time),                       # 1 year before, up to backtest
                (at_time - (365 * 24 * 3600), at_time + (365 * 24 * 3600)),   # Full range
            ]
        else:
            time_windows = [
                (at_time - base_window, at_time + base_window),               # 7 days before/after
                (at_time - base_window * 2, at_time + base_window * 2),        # 14 days before/after
                (at_time - base_window * 4, at_time + base_window * 4),       # 28 days before/after
                (at_time - (90 * 24 * 3600), at_time + (90 * 24 * 3600)),    # 90 days before/after
                (at_time - (180 * 24 * 3600), at_time + (180 * 24 * 3600)),  # 180 days before/after
                (at_time - (365 * 24 * 3600), at_time + (365 * 24 * 3600)),  # Full range
            ]
        
        # Track markets we've already seen to avoid duplicates
        seen_market_ids = set()  # Use market_ticker as unique identifier
        filtered_markets = []
        
        # Try each time window progressively
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
            consecutive_empty_pages = 0  # Track empty pages for early exit
            markets_found_in_this_window = 0  # Track how many we found in this specific window
            
            while page_count < max_pages_per_window:
                api_params['offset'] = offset
                api_params['limit'] = min(limit, 100)
                
                response = await self._call_api(self._real_api.markets.get_markets, api_params)
                
                if not response.markets:
                    break
                
                page_count += 1
                new_markets_in_window = 0
                
                for market in response.markets:
                    # Skip duplicates
                    market_id = getattr(market, 'market_ticker', None) or getattr(market, 'event_ticker', None)
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
                
                # Safer early exit: only exit if we've checked enough AND haven't found any markets
                if new_markets_in_window == 0:
                    consecutive_empty_pages += 1
                    # Only exit early if:
                    # 1. We've checked at least 5 pages (500+ markets), AND
                    # 2. We've had 3 consecutive empty pages, AND
                    # 3. We haven't found ANY markets in this window yet
                    if (consecutive_empty_pages >= 3 and 
                        page_count >= 5 and 
                        markets_found_in_this_window == 0):
                        # Safe to assume this window is empty
                        break
                else:
                    consecutive_empty_pages = 0  # Reset counter when we find markets
            
            if original_limit and len(filtered_markets) >= original_limit:
                break
            
            if not original_limit and len(filtered_markets) >= 500:
                break
        
        # Convert filtered markets to HistoricalKalshiMarket
        historical_markets = []
        
        for market in filtered_markets:
            historical_market = HistoricalKalshiMarket.from_market(market, at_time)
            historical_markets.append(historical_market)
        
        # Apply original limit if specified (after filtering)
        if original_limit and original_limit < len(filtered_markets):
            filtered_markets = filtered_markets[:original_limit]
        
        return HistoricalKalshiMarketsResponse(
            markets=filtered_markets,
            total_at_time=len(filtered_markets),
            backtest_time=at_time,
        )

    async def get_orderbooks(self, params: dict):
        """Get Kalshi orderbook history."""
        # Cap end_time at backtest time (Kalshi uses milliseconds)
        self._cap_time_at_backtest(params, 'end_time', is_milliseconds=True)
        return await self._call_api(self._real_api.orderbooks.get_orderbooks, params)

    async def get_trades(self, params: dict):
        """Get Kalshi trade history."""
        # Cap end_time at backtest time (Kalshi trades use seconds)
        self._cap_time_at_backtest(params, 'end_time', is_milliseconds=False)
        return await self._call_api(self._real_api.trades.get_trades, params)

    # Simulated order methods
    def buy(self, ticker: str, quantity: Decimal, price: Decimal):
        """Place a buy order (simulated, executes against portfolio)."""
        self._portfolio.buy(
            platform=self.platform,
            token_id=ticker,
            quantity=Decimal(quantity),
            price=Decimal(price),
            timestamp=self._clock.current_time,
        )

    def sell(self, ticker: str, quantity: Decimal, price: Decimal):
        """Place a sell order (simulated, executes against portfolio)."""
        self._portfolio.sell(
            platform=self.platform,
            token_id=ticker,
            quantity=Decimal(quantity),
            price=Decimal(price),
            timestamp=self._clock.current_time,
        )

