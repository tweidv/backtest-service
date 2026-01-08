"""Polymarket namespace classes matching Dome's structure: dome.polymarket.markets.*, dome.polymarket.orders.*, etc."""

from decimal import Decimal
from typing import TYPE_CHECKING

from .base_api import BasePlatformAPI
from .models import HistoricalMarketsResponse
from .platform_api_impl import (
    _get_markets_impl,
    _get_market_price_impl,
    _get_candlesticks_impl,
    _get_orderbooks_impl,
)

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ..simulation.clock import SimulationClock
    from ..simulation.portfolio import Portfolio


class PolymarketMarketsNamespace(BasePlatformAPI):
    """dome.polymarket.markets.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limit: float = 1.1
    ):
        super().__init__("polymarket", real_client, clock, portfolio, rate_limit)
        self._real_api = real_client.polymarket

    async def get_markets(self, params: dict = None) -> HistoricalMarketsResponse:
        """
        Get markets that existed at the current backtest time.
        
        Matches: dome.polymarket.markets.get_markets()
        """
        return await _get_markets_impl(self, params)

    async def get_market_price(self, params: dict) -> dict:
        """
        Get market price at backtest time.
        
        Matches: dome.polymarket.markets.get_market_price()
        """
        return await _get_market_price_impl(self, params)

    async def get_candlesticks(self, params: dict) -> dict:
        """
        Get candlestick data up to backtest time.
        
        Matches: dome.polymarket.markets.get_candlesticks()
        """
        return await _get_candlesticks_impl(self, params)

    async def get_orderbooks(self, params: dict) -> dict:
        """
        Get orderbook history up to backtest time.
        
        Matches: dome.polymarket.markets.get_orderbooks()
        """
        return await _get_orderbooks_impl(self, params)

    def buy(self, token_id: str, quantity: Decimal, price: Decimal):
        """
        Simulate buying tokens (backtest only - convenience method).
        
        Note: Dome doesn't have trading methods (data API only).
        This is a convenience wrapper around portfolio.buy().
        """
        self._portfolio.buy(
            platform=self.platform,
            token_id=token_id,
            quantity=Decimal(quantity),
            price=Decimal(price),
            timestamp=self._clock.current_time,
        )

    def sell(self, token_id: str, quantity: Decimal, price: Decimal):
        """
        Simulate selling tokens (backtest only - convenience method).
        
        Note: Dome doesn't have trading methods (data API only).
        This is a convenience wrapper around portfolio.sell().
        """
        self._portfolio.sell(
            platform=self.platform,
            token_id=token_id,
            quantity=Decimal(quantity),
            price=Decimal(price),
            timestamp=self._clock.current_time,
        )


class PolymarketOrdersNamespace(BasePlatformAPI):
    """dome.polymarket.orders.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limit: float = 1.1
    ):
        super().__init__("polymarket", real_client, clock, portfolio, rate_limit)
        self._real_api = real_client.polymarket

    async def get_orders(self, params: dict = None) -> dict:
        """
        Get orders up to backtest time.
        
        Matches: dome.polymarket.orders.get_orders()
        """
        params = params or {}
        at_time = self._clock.current_time
        
        # Cap end_time at backtest time to prevent lookahead
        if 'end_time' in params:
            params['end_time'] = min(params['end_time'], at_time)
        else:
            params['end_time'] = at_time
        
        # Cap start_time if provided
        if 'start_time' in params:
            params['start_time'] = min(params['start_time'], at_time)
        
        return await self._call_api(self._real_api.orders.get_orders, params)


class PolymarketWalletNamespace(BasePlatformAPI):
    """dome.polymarket.wallet.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limit: float = 1.1
    ):
        super().__init__("polymarket", real_client, clock, portfolio, rate_limit)
        self._real_api = real_client.polymarket

    async def get_wallet_pnl(self, params: dict) -> dict:
        """
        Get wallet PnL up to backtest time.
        
        Matches: dome.polymarket.wallet.get_wallet_pnl()
        """
        params = params.copy()
        at_time = self._clock.current_time
        
        # Cap end_time at backtest time
        if 'end_time' in params:
            params['end_time'] = min(params['end_time'], at_time)
        else:
            params['end_time'] = at_time
        
        # Cap start_time if provided
        if 'start_time' in params:
            params['start_time'] = min(params['start_time'], at_time)
        
        return await self._call_api(self._real_api.wallet.get_wallet_pnl, params)


class PolymarketActivityNamespace(BasePlatformAPI):
    """dome.polymarket.activity.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limit: float = 1.1
    ):
        super().__init__("polymarket", real_client, clock, portfolio, rate_limit)
        self._real_api = real_client.polymarket

    async def get_activity(self, params: dict = None) -> dict:
        """
        Get activity up to backtest time.
        
        Matches: dome.polymarket.activity.get_activity()
        """
        params = params or {}
        at_time = self._clock.current_time
        
        # Cap end_time at backtest time
        if 'end_time' in params:
            params['end_time'] = min(params['end_time'], at_time)
        else:
            params['end_time'] = at_time
        
        # Cap start_time if provided
        if 'start_time' in params:
            params['start_time'] = min(params['start_time'], at_time)
        
        return await self._call_api(self._real_api.activity.get_activity, params)


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

