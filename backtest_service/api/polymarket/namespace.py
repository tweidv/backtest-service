"""Polymarket main namespace: dome.polymarket.*"""

from typing import TYPE_CHECKING

from .markets import PolymarketMarketsNamespace
from .orders import PolymarketOrdersNamespace
from .wallet import PolymarketWalletNamespace
from .activity import PolymarketActivityNamespace

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ...simulation.clock import SimulationClock
    from ...simulation.portfolio import Portfolio


class PolymarketNamespace:
    """dome.polymarket.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limit: float = 1.1
    ):
        self.markets = PolymarketMarketsNamespace(real_client, clock, portfolio, rate_limit)
        self.orders = PolymarketOrdersNamespace(real_client, clock, portfolio, rate_limit)
        self.wallet = PolymarketWalletNamespace(real_client, clock, portfolio, rate_limit)
        self.activity = PolymarketActivityNamespace(real_client, clock, portfolio, rate_limit)
        # Note: websocket not implemented yet (would be for real-time, not backtesting)
        
        # Store references for convenience methods
        self._portfolio = portfolio
        self._clock = clock
    
    def buy(self, token_id: str, quantity, price, order_type: str = "taker", market_type: str = "global"):
        """Convenience method to buy tokens directly."""
        from decimal import Decimal
        self._portfolio.buy(
            platform="polymarket",
            token_id=token_id,
            quantity=Decimal(str(quantity)),
            price=Decimal(str(price)),
            timestamp=self._clock.current_time,
            order_type=order_type,
            market_type=market_type
        )
    
    def sell(self, token_id: str, quantity, price, order_type: str = "taker", market_type: str = "global"):
        """Convenience method to sell tokens directly."""
        from decimal import Decimal
        self._portfolio.sell(
            platform="polymarket",
            token_id=token_id,
            quantity=Decimal(str(quantity)),
            price=Decimal(str(price)),
            timestamp=self._clock.current_time,
            order_type=order_type,
            market_type=market_type
        )

