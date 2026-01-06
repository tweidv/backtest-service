import asyncio
import inspect
from dataclasses import dataclass
from decimal import Decimal
from typing import List, Optional
from dome_api_sdk import DomeClient

from ..simulation.clock import SimulationClock
from ..simulation.portfolio import Portfolio


@dataclass
class HistoricalMarket:
    """
    Market data adjusted for historical context.
    
    The `historical_status` reflects what the market status WAS at the
    backtest time, not what it is now.
    """
    # Original market data (pass-through)
    market_slug: str
    condition_id: str
    title: str
    start_time: int
    end_time: int
    completed_time: Optional[int]
    close_time: Optional[int]
    game_start_time: Optional[str]
    tags: List[str]
    volume_1_week: float
    volume_1_month: float
    volume_1_year: float
    volume_total: float
    resolution_source: str
    image: str
    side_a: any  # MarketSide
    side_b: any  # MarketSide
    winning_side: Optional[any]  # MarketSide or None
    status: str  # Current status from API
    
    # Historical context
    historical_status: str  # "open" or "closed" at backtest time
    was_resolved: bool  # Whether market was already resolved at backtest time
    
    @classmethod
    def from_market(cls, market, at_time: int):
        """Create HistoricalMarket from API Market, computing historical status."""
        # Determine historical status at backtest time
        if market.close_time and market.close_time <= at_time:
            historical_status = "closed"
            was_resolved = market.completed_time is not None and market.completed_time <= at_time
        else:
            historical_status = "open"
            was_resolved = False
        
        return cls(
            market_slug=market.market_slug,
            condition_id=market.condition_id,
            title=market.title,
            start_time=market.start_time,
            end_time=market.end_time,
            completed_time=market.completed_time,
            close_time=market.close_time,
            game_start_time=market.game_start_time,
            tags=market.tags,
            volume_1_week=market.volume_1_week,
            volume_1_month=market.volume_1_month,
            volume_1_year=market.volume_1_year,
            volume_total=market.volume_total,
            resolution_source=market.resolution_source,
            image=market.image,
            side_a=market.side_a,
            side_b=market.side_b,
            winning_side=market.winning_side if was_resolved else None,
            status=market.status,
            historical_status=historical_status,
            was_resolved=was_resolved,
        )


@dataclass
class HistoricalMarketsResponse:
    """Response from get_markets with historical filtering applied."""
    markets: List[HistoricalMarket]
    total_at_time: int  # How many markets existed at backtest time
    backtest_time: int  # The time used for filtering


@dataclass
class HistoricalKalshiMarket:
    """
    Kalshi market data adjusted for historical context.
    """
    event_ticker: str
    market_ticker: str
    title: str
    start_time: int
    end_time: int
    close_time: Optional[int]
    status: str  # Current status from API
    last_price: float
    volume: float
    volume_24h: float
    result: Optional[str]  # Current result from API
    
    # Historical context
    historical_status: str  # "open" or "closed" at backtest time
    was_resolved: bool
    historical_result: Optional[str]  # Result only if resolved at backtest time
    
    @classmethod
    def from_market(cls, market, at_time: int):
        """Create HistoricalKalshiMarket from API KalshiMarketData."""
        if market.close_time and market.close_time <= at_time:
            historical_status = "closed"
            was_resolved = True  # Kalshi close_time indicates resolution
            historical_result = market.result
        else:
            historical_status = "open"
            was_resolved = False
            historical_result = None
        
        return cls(
            event_ticker=market.event_ticker,
            market_ticker=market.market_ticker,
            title=market.title,
            start_time=market.start_time,
            end_time=market.end_time,
            close_time=market.close_time,
            status=market.status,
            last_price=market.last_price,
            volume=market.volume,
            volume_24h=market.volume_24h,
            result=market.result,
            historical_status=historical_status,
            was_resolved=was_resolved,
            historical_result=historical_result,
        )


@dataclass
class HistoricalKalshiMarketsResponse:
    """Response from Kalshi get_markets with historical filtering applied."""
    markets: List[HistoricalKalshiMarket]
    total_at_time: int
    backtest_time: int


class PlatformAPI:
    """Wraps a platform's API, injecting at_time from clock"""
    
    def __init__(self, platform: str, real_client: DomeClient, clock: SimulationClock, portfolio: Portfolio, rate_limit: float = 1.1):
        self.platform = platform
        self._client = real_client
        self._clock = clock
        self._portfolio = portfolio
        self._real_api = getattr(real_client, platform)
        self._rate_limit = rate_limit  # seconds between API calls

    async def _call_api(self, method, params: dict):
        """Call API method with rate limiting, handling both sync and async methods"""
        await asyncio.sleep(self._rate_limit)
        result = method(params)
        # If the SDK returns a coroutine, await it
        if inspect.iscoroutine(result):
            return await result
        return result

    def _market_existed_at_time(self, market, at_time: int) -> bool:
        """Check if market existed (was created) at the given time."""
        return market.start_time <= at_time

    def _market_was_open_at_time(self, market, at_time: int) -> bool:
        """Check if market was open (tradeable) at the given time."""
        if market.start_time > at_time:
            return False  # Hadn't started yet
        if market.close_time and market.close_time <= at_time:
            return False  # Already closed
        return True

    def _market_was_closed_at_time(self, market, at_time: int) -> bool:
        """Check if market was already closed at the given time."""
        if market.start_time > at_time:
            return False  # Didn't exist yet
        if market.close_time and market.close_time <= at_time:
            return True  # Was closed
        return False

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
        
        Args:
            params: Same params as dome API (tags, min_volume, limit, offset, status, etc.)
                   The 'status' param is intercepted and applied historically.
        
        Returns:
            HistoricalMarketsResponse with filtered markets and metadata
        """
        params = params or {}
        at_time = self._clock.current_time
        
        # Extract and remove status filter - we'll apply it ourselves
        requested_status = params.pop('status', None)
        
        # We need to fetch from API without status filter because:
        # - A market that is "closed" NOW might have been "open" at backtest time
        # - A market that is "open" NOW might not have existed at backtest time
        # So we fetch more broadly and filter client-side
        
        # To be efficient, if user wants "closed" markets at historical time,
        # we can still ask API for "closed" (subset of what we need)
        # But if user wants "open" at historical time, we need BOTH statuses
        api_params = params.copy()
        
        # Fetch from real API
        response = await self._call_api(self._real_api.markets.get_markets, api_params)
        
        # Filter markets based on backtest time
        filtered_markets = []
        
        for market in response.markets:
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
            
            # Convert to HistoricalMarket with proper historical context
            historical_market = HistoricalMarket.from_market(market, at_time)
            filtered_markets.append(historical_market)
        
        return HistoricalMarketsResponse(
            markets=filtered_markets,
            total_at_time=len(filtered_markets),
            backtest_time=at_time,
        )

    async def get_market(self, params: dict):
        params['at_time'] = params.get('at_time', self._clock.current_time)
        return await self._call_api(self._real_api.markets.get_market, params)

    async def get_market_price(self, params: dict):
        params['at_time'] = params.get('at_time', self._clock.current_time)
        return await self._call_api(self._real_api.markets.get_market_price, params)

    async def get_orderbook_history(self, params: dict):
        params['at_time'] = params.get('at_time', self._clock.current_time)
        return await self._call_api(self._real_api.markets.get_orderbook_history, params)

    async def get_trade_history(self, params: dict):
        params['at_time'] = params.get('at_time', self._clock.current_time)
        return await self._call_api(self._real_api.markets.get_trade_history, params)

    # Simulated order methods - execute against portfolio
    def buy(self, token_id: str, quantity: Decimal, price: Decimal):
        self._portfolio.buy(
            platform=self.platform,
            token_id=token_id,
            quantity=Decimal(quantity),
            price=Decimal(price),
            timestamp=self._clock.current_time,
        )

    def sell(self, token_id: str, quantity: Decimal, price: Decimal):
        self._portfolio.sell(
            platform=self.platform,
            token_id=token_id,
            quantity=Decimal(quantity),
            price=Decimal(price),
            timestamp=self._clock.current_time,
        )


class KalshiAPI:
    """Wraps Kalshi API with historical filtering for backtesting."""
    
    def __init__(self, real_client: DomeClient, clock: SimulationClock, portfolio: Portfolio, rate_limit: float = 1.1):
        self.platform = "kalshi"
        self._client = real_client
        self._clock = clock
        self._portfolio = portfolio
        self._real_api = real_client.kalshi
        self._rate_limit = rate_limit

    async def _call_api(self, method, params: dict):
        """Call API method with rate limiting."""
        await asyncio.sleep(self._rate_limit)
        result = method(params)
        if inspect.iscoroutine(result):
            return await result
        return result

    def _market_existed_at_time(self, market, at_time: int) -> bool:
        return market.start_time <= at_time

    def _market_was_open_at_time(self, market, at_time: int) -> bool:
        if market.start_time > at_time:
            return False
        if market.close_time and market.close_time <= at_time:
            return False
        return True

    def _market_was_closed_at_time(self, market, at_time: int) -> bool:
        if market.start_time > at_time:
            return False
        if market.close_time and market.close_time <= at_time:
            return True
        return False

    async def get_markets(self, params: dict = None) -> HistoricalKalshiMarketsResponse:
        """
        Get Kalshi markets that existed at the current backtest time.
        
        Same historical filtering logic as Polymarket get_markets.
        """
        params = params or {}
        at_time = self._clock.current_time
        
        requested_status = params.pop('status', None)
        api_params = params.copy()
        
        response = await self._call_api(self._real_api.markets.get_markets, api_params)
        
        filtered_markets = []
        
        for market in response.markets:
            if not self._market_existed_at_time(market, at_time):
                continue
            
            if requested_status == 'open':
                if not self._market_was_open_at_time(market, at_time):
                    continue
            elif requested_status == 'closed':
                if not self._market_was_closed_at_time(market, at_time):
                    continue
            
            historical_market = HistoricalKalshiMarket.from_market(market, at_time)
            filtered_markets.append(historical_market)
        
        return HistoricalKalshiMarketsResponse(
            markets=filtered_markets,
            total_at_time=len(filtered_markets),
            backtest_time=at_time,
        )

    async def get_orderbooks(self, params: dict):
        """Get Kalshi orderbook history."""
        # Cap end_time at backtest time
        if 'end_time' in params:
            params['end_time'] = min(params['end_time'], self._clock.current_time * 1000)  # Kalshi uses ms
        return await self._call_api(self._real_api.markets.get_orderbooks, params)

    # Simulated order methods
    def buy(self, ticker: str, quantity: Decimal, price: Decimal):
        self._portfolio.buy(
            platform=self.platform,
            token_id=ticker,
            quantity=Decimal(quantity),
            price=Decimal(price),
            timestamp=self._clock.current_time,
        )

    def sell(self, ticker: str, quantity: Decimal, price: Decimal):
        self._portfolio.sell(
            platform=self.platform,
            token_id=ticker,
            quantity=Decimal(quantity),
            price=Decimal(price),
            timestamp=self._clock.current_time,
        )


class DomeBacktestClient:
    """Drop-in replacement for DomeClient that replays historical data"""
    
    def __init__(self, api_key: str, clock: SimulationClock, portfolio: Portfolio):
        self._real_client = DomeClient({"api_key": api_key})
        self._clock = clock
        self._portfolio = portfolio
        
        self.polymarket = PlatformAPI('polymarket', self._real_client, clock, portfolio)
        self.kalshi = KalshiAPI(self._real_client, clock, portfolio)

