"""Data models for historical market data with backtest context."""

from dataclasses import dataclass
from typing import List, Optional


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

