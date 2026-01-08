"""Kalshi namespace classes matching Dome's structure: dome.kalshi.markets.*, dome.kalshi.orderbooks.*, etc."""

from decimal import Decimal
from typing import TYPE_CHECKING

from .base_api import BasePlatformAPI
from .models import HistoricalKalshiMarket, HistoricalKalshiMarketsResponse

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ..simulation.clock import SimulationClock
    from ..simulation.portfolio import Portfolio


async def _get_kalshi_markets_impl(self: BasePlatformAPI, params: dict = None) -> HistoricalKalshiMarketsResponse:
    """Implementation of get_markets for Kalshi - extracted for reuse."""
    params = params or {}
    at_time = self._clock.current_time
    
    requested_status = params.pop('status', None)
    original_limit = params.get('limit', 100)
    
    base_window = 7 * 24 * 3600
    if requested_status == 'open':
        time_windows = [
            (at_time - base_window, at_time + base_window * 3),
            (at_time - base_window * 2, at_time + base_window * 6),
            (at_time - base_window * 4, at_time + base_window * 12),
            (at_time - (90 * 24 * 3600), at_time + (180 * 24 * 3600)),
            (at_time - (180 * 24 * 3600), at_time + (365 * 24 * 3600)),
            (at_time - (365 * 24 * 3600), at_time + (365 * 24 * 3600)),
        ]
    elif requested_status == 'closed':
        time_windows = [
            (at_time - base_window * 2, at_time),
            (at_time - base_window * 4, at_time),
            (at_time - (90 * 24 * 3600), at_time),
            (at_time - (180 * 24 * 3600), at_time),
            (at_time - (365 * 24 * 3600), at_time),
            (at_time - (365 * 24 * 3600), at_time + (365 * 24 * 3600)),
        ]
    else:
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
        historical_market = HistoricalKalshiMarket.from_market(market, at_time)
        historical_markets.append(historical_market)
    
    if original_limit and original_limit < len(historical_markets):
        historical_markets = historical_markets[:original_limit]
    
    return HistoricalKalshiMarketsResponse(
        markets=historical_markets,
        total_at_time=len(historical_markets),
        backtest_time=at_time,
    )


class KalshiMarketsNamespace(BasePlatformAPI):
    """dome.kalshi.markets.* namespace - matches Dome's structure exactly."""
    
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
        
        Matches: dome.kalshi.markets.get_markets()
        """
        return await _get_kalshi_markets_impl(self, params)

    def buy(self, ticker: str, quantity: Decimal, price: Decimal):
        """
        Simulate buying tokens (backtest only - convenience method).
        
        Note: Dome doesn't have trading methods (data API only).
        This is a convenience wrapper around portfolio.buy().
        """
        self._portfolio.buy(
            platform=self.platform,
            token_id=ticker,
            quantity=Decimal(quantity),
            price=Decimal(price),
            timestamp=self._clock.current_time,
        )

    def sell(self, ticker: str, quantity: Decimal, price: Decimal):
        """
        Simulate selling tokens (backtest only - convenience method).
        
        Note: Dome doesn't have trading methods (data API only).
        This is a convenience wrapper around portfolio.sell().
        """
        self._portfolio.sell(
            platform=self.platform,
            token_id=ticker,
            quantity=Decimal(quantity),
            price=Decimal(price),
            timestamp=self._clock.current_time,
        )


class KalshiOrderbooksNamespace(BasePlatformAPI):
    """dome.kalshi.orderbooks.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limit: float = 1.1
    ):
        super().__init__("kalshi", real_client, clock, portfolio, rate_limit)
        self._real_api = real_client.kalshi

    async def get_orderbooks(self, params: dict) -> dict:
        """
        Get Kalshi orderbook history up to backtest time.
        
        Matches: dome.kalshi.orderbooks.get_orderbooks()
        """
        self._cap_time_at_backtest(params, 'end_time', is_milliseconds=True)
        return await self._call_api(self._real_api.orderbooks.get_orderbooks, params)


class KalshiNamespace:
    """dome.kalshi.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limit: float = 1.1
    ):
        self.markets = KalshiMarketsNamespace(real_client, clock, portfolio, rate_limit)
        self.orderbooks = KalshiOrderbooksNamespace(real_client, clock, portfolio, rate_limit)

