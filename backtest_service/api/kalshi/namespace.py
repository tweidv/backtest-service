"""Kalshi main namespace: dome.kalshi.*"""

from typing import TYPE_CHECKING

from .markets import KalshiMarketsNamespace
from .orderbooks import KalshiOrderbooksNamespace
from .trades import KalshiTradesNamespace

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ...simulation.clock import SimulationClock
    from ...simulation.portfolio import Portfolio


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
        self.trades = KalshiTradesNamespace(real_client, clock, portfolio, rate_limit)

