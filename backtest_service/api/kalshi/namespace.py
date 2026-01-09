"""Kalshi main namespace: dome.kalshi.*"""

from typing import TYPE_CHECKING, Union

from .markets import KalshiMarketsNamespace
from .orderbooks import KalshiOrderbooksNamespace
from .trades import KalshiTradesNamespace

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ...simulation.clock import SimulationClock
    from ...simulation.portfolio import Portfolio
    from ..rate_limiter import RateLimiter


class KalshiNamespace:
    """dome.kalshi.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limiter: Union["RateLimiter", float, None] = None
    ):
        self.markets = KalshiMarketsNamespace(real_client, clock, portfolio, rate_limiter)
        self.orderbooks = KalshiOrderbooksNamespace(real_client, clock, portfolio, rate_limiter)
        self.trades = KalshiTradesNamespace(real_client, clock, portfolio, rate_limiter)
        
        # Store references for convenience methods
        self._portfolio = portfolio
        self._clock = clock
    
    def buy(self, ticker: str, quantity, price, side: str = "YES"):
        """Convenience method to buy Kalshi contracts directly."""
        from decimal import Decimal
        # For Kalshi, use composite key with side
        position_key = f"{ticker}:{side.upper()}"
        self._portfolio.buy(
            platform="kalshi",
            token_id=position_key,
            quantity=Decimal(str(quantity)),
            price=Decimal(str(price)),
            timestamp=self._clock.current_time,
            order_type="taker",  # Default to taker
            market_type="global"  # Not applicable for Kalshi
        )
    
    def sell(self, ticker: str, quantity, price, side: str = "YES"):
        """Convenience method to sell Kalshi contracts directly."""
        from decimal import Decimal
        # For Kalshi, use composite key with side
        position_key = f"{ticker}:{side.upper()}"
        self._portfolio.sell(
            platform="kalshi",
            token_id=position_key,
            quantity=Decimal(str(quantity)),
            price=Decimal(str(price)),
            timestamp=self._clock.current_time,
            order_type="taker",  # Default to taker
            market_type="global"  # Not applicable for Kalshi
        )

