"""Crypto prices main namespace: dome.crypto_prices.*"""

from typing import TYPE_CHECKING

from .binance import BinanceNamespace
from .chainlink import ChainlinkNamespace

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ...simulation.clock import SimulationClock
    from ...simulation.portfolio import Portfolio


class CryptoPricesNamespace:
    """dome.crypto_prices.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limit: float = 1.1
    ):
        self.binance = BinanceNamespace(real_client, clock, portfolio, rate_limit)
        self.chainlink = ChainlinkNamespace(real_client, clock, portfolio, rate_limit)

