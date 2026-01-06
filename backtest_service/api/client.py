import asyncio
import inspect
from decimal import Decimal
from dome_api_sdk import DomeClient

from ..simulation.clock import SimulationClock
from ..simulation.portfolio import Portfolio


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


class DomeBacktestClient:
    """Drop-in replacement for DomeClient that replays historical data"""
    
    def __init__(self, api_key: str, clock: SimulationClock, portfolio: Portfolio):
        self._real_client = DomeClient({"api_key": api_key})
        self._clock = clock
        self._portfolio = portfolio
        
        self.polymarket = PlatformAPI('polymarket', self._real_client, clock, portfolio)
        self.kalshi = PlatformAPI('kalshi', self._real_client, clock, portfolio)

