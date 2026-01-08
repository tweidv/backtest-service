"""Kalshi markets namespace: dome.kalshi.markets.*"""

from decimal import Decimal
from typing import TYPE_CHECKING

from ..base_api import BasePlatformAPI
from ..models import HistoricalKalshiMarket, HistoricalKalshiMarketsResponse

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ...simulation.clock import SimulationClock
    from ...simulation.portfolio import Portfolio


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
        self._real_client = real_client  # Store for orderbook access

    async def get_markets(self, params: dict = None) -> HistoricalKalshiMarketsResponse:
        """
        Get Kalshi markets that existed at the current backtest time.
        
        Matches: dome.kalshi.markets.get_markets()
        
        Parameters (from Dome docs):
        - market_ticker: Optional - Filter by market ticker(s) - can be array
        - event_ticker: Optional - Filter by event ticker(s) - can be array
        - search: Optional - Search markets by keywords in title/description (URL encoded)
        - status: Optional - Filter by status (open/closed)
        - min_volume: Optional - Filter markets with volume >= this amount (in dollars)
        - limit: Optional - Number of markets to return (1-100, default: 10)
        - offset: Optional - Number of markets to skip for pagination
        - start_time: Optional - Unix timestamp (seconds) - filter markets by creation time
        - end_time: Optional - Unix timestamp (seconds) - filter markets by creation time
        """
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

    async def create_order(
        self,
        ticker: str,
        side: str,
        action: str,
        count: int,
        order_type: str = "limit",
        yes_price: int = None,
        no_price: int = None,
        client_order_id: str = None,
    ) -> dict:
        """
        Create an order - matches kalshi SDK API signature.
        
        Matches: kalshi.KalshiClient.create_order()
        
        Args:
            ticker: Market ticker (required)
            side: "yes" or "no" (required)
            action: "buy" or "sell" (required)
            count: Number of contracts (integer, required)
            order_type: "limit" or "market" (default: "limit")
            yes_price: Price in cents (0-100) for YES side (required for limit orders)
            no_price: Price in cents (0-100) for NO side (required for limit orders)
            client_order_id: Optional custom order ID
        
        Returns:
            Simulated order response matching kalshi SDK structure
        
        Example:
            order = await dome.kalshi.markets.create_order(
                ticker="KXNFLGAME-25AUG16ARIDEN-ARI",
                side="yes",
                action="buy",
                count=100,
                order_type="limit",
                yes_price=75  # cents
            )
        """
        # Validate side
        if side.lower() not in ["yes", "no"]:
            raise ValueError(f"side must be 'yes' or 'no', got: {side}")
        
        # Validate action
        if action.lower() not in ["buy", "sell"]:
            raise ValueError(f"action must be 'buy' or 'sell', got: {action}")
        
        # Validate order_type
        if order_type not in ["limit", "market"]:
            raise ValueError(f"order_type must be 'limit' or 'market', got: {order_type}")
        
        # Validate price for limit orders
        if order_type == "limit":
            if side.lower() == "yes" and yes_price is None:
                raise ValueError("yes_price is required for YES side limit orders")
            if side.lower() == "no" and no_price is None:
                raise ValueError("no_price is required for NO side limit orders")
            if yes_price is not None and (yes_price < 0 or yes_price > 100):
                raise ValueError(f"yes_price must be between 0-100 cents, got: {yes_price}")
            if no_price is not None and (no_price < 0 or no_price > 100):
                raise ValueError(f"no_price must be between 0-100 cents, got: {no_price}")
        
        # Get price (convert cents to decimal)
        if order_type == "market":
            limit_price = None
        else:
            if side.lower() == "yes":
                limit_price = Decimal(yes_price) / Decimal(100)  # Convert cents to 0-1
            else:
                limit_price = Decimal(no_price) / Decimal(100)  # Convert cents to 0-1
        
        # Initialize order simulation if needed
        self._init_order_simulation()
        
        # Determine actual side for order (YES/NO)
        order_side = side.upper()
        
        # Create and execute order
        # Kalshi doesn't have market types like Polymarket, so use "global"
        # Map "market" to "FOK" (Dome API format)
        mapped_order_type = "FOK" if order_type == "market" else "GTC"
        
        simulated_order = await self._order_manager.create_order(
            token_id=ticker,
            side=order_side,
            size=Decimal(count),
            limit_price=limit_price,
            order_type=mapped_order_type,
            expiration_time_seconds=None,
            client_order_id=client_order_id,
            platform=self.platform,
            market_type="global",  # Not applicable for Kalshi
        )
        
        # Return response matching kalshi SDK structure
        return {
            "order_id": simulated_order.order_id,
            "client_order_id": simulated_order.client_order_id,
            "ticker": simulated_order.token_id,
            "side": simulated_order.side.lower(),
            "action": action.lower(),
            "count": int(simulated_order.size),
            "type": order_type,
            "yes_price": int(simulated_order.limit_price * 100) if simulated_order.limit_price else None,
            "no_price": int((Decimal(1) - simulated_order.limit_price) * 100) if simulated_order.limit_price else None,
            "status": simulated_order.status.value,
            "filled_count": int(simulated_order.filled_size),
            "fill_price": int(simulated_order.fill_price * 100) if simulated_order.fill_price else None,
            "created_time": simulated_order.created_time,
        }

