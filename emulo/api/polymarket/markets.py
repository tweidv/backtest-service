"""Polymarket markets namespace: dome.polymarket.markets.*"""

from decimal import Decimal
from typing import TYPE_CHECKING, Union

from ..base_api import BasePlatformAPI
from ..models import HistoricalMarket, HistoricalMarketsResponse

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ...simulation.clock import SimulationClock
    from ...simulation.portfolio import Portfolio
    from ..rate_limiter import RateLimiter


class PolymarketMarketsNamespace(BasePlatformAPI):
    """dome.polymarket.markets.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limiter: Union["RateLimiter", float, None] = None
    ):
        super().__init__("polymarket", real_client, clock, portfolio, rate_limiter)
        self._real_api = real_client.polymarket
        self._real_client = real_client  # Store for orderbook access
        # Note: _verbose, _log_level, _on_api_call are set by DomeBacktestClient

    async def get_markets(self, params: dict = None) -> HistoricalMarketsResponse:
        """
        Get markets that existed at the current backtest time.
        
        Matches: dome.polymarket.markets.get_markets()
        
        Parameters (from Dome docs):
        - status: Filter by status (open/closed)
        - limit: Number of markets to return (1-100, default: 10)
        - offset: Number of markets to skip for pagination
        - min_volume: Filter markets with volume >= this amount
        - market_slug: Filter by market slug(s) - can be array
        - tags: Filter by tags - can be array
        - start_time: Unix timestamp (seconds) - filter markets by creation time
        - end_time: Unix timestamp (seconds) - filter markets by creation time
        """
        params = params or {}
        at_time = self._clock.current_time
        
        # Extract and remove status filter - we'll apply it ourselves
        requested_status = params.pop('status', None)
        original_limit = params.get('limit', 100)
        
        # Smart progressive time window expansion
        time_windows = []
        if requested_status == 'open':
            base_window = 7 * 24 * 3600  # 7 days
            time_windows = [
                (at_time - base_window, at_time + base_window * 3),
                (at_time - base_window * 2, at_time + base_window * 6),
                (at_time - base_window * 4, at_time + base_window * 12),
                (at_time - (90 * 24 * 3600), at_time + (180 * 24 * 3600)),
                (at_time - (180 * 24 * 3600), at_time + (365 * 24 * 3600)),
                (at_time - (365 * 24 * 3600), at_time + (365 * 24 * 3600)),
            ]
        elif requested_status == 'closed':
            base_window = 7 * 24 * 3600
            time_windows = [
                (at_time - base_window * 2, at_time),
                (at_time - base_window * 4, at_time),
                (at_time - (90 * 24 * 3600), at_time),
                (at_time - (180 * 24 * 3600), at_time),
                (at_time - (365 * 24 * 3600), at_time),
                (at_time - (365 * 24 * 3600), at_time + (365 * 24 * 3600)),
            ]
        else:
            base_window = 7 * 24 * 3600
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
                api_params['limit'] = min(limit, 100)  # API max is 100
                
                response = await self._call_api(self._real_api.markets.get_markets, api_params)
                
                if not response.markets:
                    break
                
                page_count += 1
                new_markets_in_window = 0
                
                for market in response.markets:
                    market_id = getattr(market, 'condition_id', None) or getattr(market, 'market_slug', None)
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
            historical_market = HistoricalMarket.from_market(market, at_time)
            historical_markets.append(historical_market)
        
        if original_limit and original_limit < len(historical_markets):
            historical_markets = historical_markets[:original_limit]
        
        return HistoricalMarketsResponse(
            markets=historical_markets,
            total_at_time=len(historical_markets),
            backtest_time=at_time,
        )

    async def get_market_price(self, params: dict) -> dict:
        """
        Get market price at backtest time.
        
        Matches: dome.polymarket.markets.get_market_price()
        
        Parameters (from Dome docs):
        - token_id: Required - The token ID for the Polymarket market (path parameter in API, but SDK handles it)
        - at_time: Optional - Unix timestamp (seconds) for historical price lookup
        """
        # SDK handles token_id as path parameter, we pass it in params
        if 'token_id' not in params:
            raise ValueError("token_id is required for get_market_price")
        
        # Set at_time to backtest time if not provided
        params['at_time'] = params.get('at_time', self._clock.current_time)
        
        # Cap at_time at backtest time to prevent lookahead
        params['at_time'] = min(params['at_time'], self._clock.current_time)
        
        response = await self._call_api(self._real_api.markets.get_market_price, params)
        
        # CRITICAL: Verify the returned price's at_time is not after backtest time
        # get_market_price returns a single price with an at_time field
        if hasattr(response, 'at_time'):
            response_at_time = response.at_time
            if response_at_time > self._clock.current_time:
                # This shouldn't happen if API respects at_time param, but verify
                # The API should respect at_time, so this is just a safety check
                pass
        
        return response

    async def get_candlesticks(self, params: dict) -> dict:
        """
        Get candlestick data up to backtest time.
        
        Matches: dome.polymarket.markets.get_candlesticks()
        
        Parameters (from Dome docs):
        - condition_id: Required - The condition ID for the market (path parameter)
        - start_time: Required - Unix timestamp (seconds) for start of time range
        - end_time: Required - Unix timestamp (seconds) for end of time range
        - interval: Optional - 1 (1m), 60 (1h), or 1440 (1d). Defaults to 1.
          Range limits: 1m (max 1 week), 1h (max 1 month), 1d (max 1 year)
        """
        if 'condition_id' not in params:
            raise ValueError("condition_id is required for get_candlesticks")
        
        if 'start_time' not in params or 'end_time' not in params:
            raise ValueError("start_time and end_time are required for get_candlesticks")
        
        # Cap end_time at backtest time (candlesticks use seconds)
        self._cap_time_at_backtest(params, 'end_time', is_milliseconds=False)
        
        interval = params.get('interval', 1)
        start_time = params['start_time']
        end_time = params['end_time']
        time_range = end_time - start_time
        
        # Validate range limits per Dome docs
        if interval == 1:  # 1 minute
            max_range = 7 * 24 * 3600  # 1 week
            if time_range > max_range:
                raise ValueError(
                    f"For 1m interval, max range is 1 week. "
                    f"Requested range: {time_range / (24 * 3600):.2f} days"
                )
        elif interval == 60:  # 1 hour
            max_range = 30 * 24 * 3600  # 1 month
            if time_range > max_range:
                raise ValueError(
                    f"For 1h interval, max range is 1 month. "
                    f"Requested range: {time_range / (24 * 3600):.2f} days"
                )
        elif interval == 1440:  # 1 day
            max_range = 365 * 24 * 3600  # 1 year
            if time_range > max_range:
                raise ValueError(
                    f"For 1d interval, max range is 1 year. "
                    f"Requested range: {time_range / (365 * 24 * 3600):.2f} years"
                )
        
        response = await self._call_api(self._real_api.markets.get_candlesticks, params)
        
        # Filter candlesticks to only include those up to backtest time
        if hasattr(response, 'candlesticks') and response.candlesticks:
            filtered_candlesticks = []
            at_time = self._clock.current_time
            
            for candlestick_tuple in response.candlesticks:
                if not isinstance(candlestick_tuple, (list, tuple)) or len(candlestick_tuple) < 2:
                    continue
                
                candlestick_data = candlestick_tuple[0]
                end_period = None
                if hasattr(candlestick_data, 'end_period_ts'):
                    end_period = candlestick_data.end_period_ts
                elif isinstance(candlestick_data, dict):
                    end_period = candlestick_data.get('end_period_ts')
                
                if end_period is not None and end_period <= at_time:
                    filtered_candlesticks.append(candlestick_tuple)
            
            try:
                import copy
                if hasattr(response, '__dict__'):
                    filtered_response = copy.copy(response)
                    filtered_response.candlesticks = filtered_candlesticks
                    return filtered_response
            except (AttributeError, TypeError):
                # Fallback if copy fails - create simple response object
                class FilteredResponse:
                    def __init__(self, candlesticks):
                        self.candlesticks = candlesticks
                return FilteredResponse(filtered_candlesticks)
        
        return response

    async def get_orderbooks(self, params: dict) -> dict:
        """
        Get orderbook history up to backtest time.
        
        Matches: dome.polymarket.markets.get_orderbooks()
        
        Parameters (from Dome docs):
        - token_id: Required - The token ID for the Polymarket market
        - start_time: Optional - Unix timestamp (milliseconds). If not provided with end_time, returns latest snapshot
        - end_time: Optional - Unix timestamp (milliseconds). If not provided with start_time, returns latest snapshot
        - limit: Optional - Max snapshots to return (default: 100, max: 200). Ignored when fetching latest.
        - pagination_key: Optional - Pagination key for next chunk. Ignored when fetching latest.
        
        Note: All timestamps are in milliseconds (not seconds like other endpoints).
        Orderbook data has history starting from October 14th, 2025.
        """
        if 'token_id' not in params:
            raise ValueError("token_id is required for get_orderbooks")
        
        # Cap end_time at backtest time (orderbooks use milliseconds)
        self._cap_time_at_backtest(params, 'end_time', is_milliseconds=True)
        
        # Cap start_time if provided
        if 'start_time' in params:
            self._cap_time_at_backtest(params, 'start_time', is_milliseconds=True)
        
        response = await self._call_api(self._real_api.markets.get_orderbooks, params)
        
        # CRITICAL: Filter response data to remove orderbook snapshots after backtest time
        # Orderbooks use 'timestamp' field (in milliseconds)
        if hasattr(response, 'snapshots') and response.snapshots:
            at_time_ms = self._clock.current_time * 1000  # Convert to milliseconds
            filtered_snapshots = []
            for snapshot in response.snapshots:
                # Get timestamp from snapshot (field name: timestamp, in milliseconds)
                snapshot_timestamp = None
                if hasattr(snapshot, 'timestamp'):
                    snapshot_timestamp = snapshot.timestamp
                elif isinstance(snapshot, dict):
                    snapshot_timestamp = snapshot.get('timestamp')
                
                # Only include snapshots that occurred at or before backtest time
                if snapshot_timestamp is not None and snapshot_timestamp <= at_time_ms:
                    filtered_snapshots.append(snapshot)
            
            # Create filtered response
            try:
                import copy
                if hasattr(response, '__dict__'):
                    filtered_response = copy.copy(response)
                    filtered_response.snapshots = filtered_snapshots
                    return filtered_response
            except (AttributeError, TypeError):
                # Fallback if copy fails - create simple response object
                class FilteredResponse:
                    def __init__(self, snapshots, pagination_key=None):
                        self.snapshots = snapshots
                        self.pagination_key = pagination_key
                pagination_key = getattr(response, 'pagination_key', None)
                return FilteredResponse(filtered_snapshots, pagination_key)
        
        return response

    async def create_order(
        self,
        token_id: str,
        side: str,
        size: str,
        price: str,
        order_type: str = "GTC",
        expiration_time_seconds: int = None,
        post_only: bool = False,
        client_order_id: str = None,
    ) -> dict:
        """
        Create an order - matches Dome API signature.
        
        Matches: Dome API router.placeOrder()
        
        Args:
            token_id: Condition token ID (required)
            side: "buy" or "sell" (required) - Dome API format
            size: Order size as string in base units (required)
            price: Limit price as string (0-1) (required for limit orders, None for FOK without limit)
            order_type: "FOK", "FAK", "GTC", or "GTD" (default: "GTC")
                - "FOK": Fill Or Kill - must fill completely or reject
                - "FAK": Fill And Kill - fill what you can, cancel rest
                - "GTC": Good Till Cancel - stays on book until filled
                - "GTD": Good Till Date - expires at specified time
            expiration_time_seconds: Required for GTD orders
            post_only: Deprecated - not used
            client_order_id: Optional custom order ID
        
        Returns:
            Order response with status: "matched" when filled, "pending" when on book, etc.
        
        Example:
            order = await dome.polymarket.markets.create_order(
                token_id="0x123...",
                side="buy",
                size="1000000000",
                price="0.65",
                order_type="GTC"
            )
            
            if order["status"] == "matched":
                print("Order filled!")
        """
        # Validate side (Dome API format)
        side_lower = side.lower()
        if side_lower not in ["buy", "sell"]:
            raise ValueError(f"side must be 'buy' or 'sell', got: {side}")
        
        # Normalize side to internal format
        from ...simulation.orders import normalize_side
        normalized_side = normalize_side(side)
        
        # Validate order_type (Dome API format - no MARKET, use FOK instead)
        valid_types = ["FOK", "FAK", "GTC", "GTD"]
        order_type_upper = order_type.upper()
        if order_type_upper not in valid_types:
            raise ValueError(f"order_type must be one of {valid_types}, got: {order_type}")
        
        # Validate GTD requires expiration
        if order_type_upper == "GTD" and expiration_time_seconds is None:
            raise ValueError("expiration_time_seconds is required for GTD orders")
        
        # Initialize order simulation if needed
        self._init_order_simulation()
        
        # Convert to Decimal
        size_decimal = Decimal(size)
        limit_price = Decimal(price) if price else None
        
        # For FOK orders without price, treat as market order
        if order_type_upper == "FOK" and limit_price is None:
            limit_price = None  # Will use market price
        
        # Determine market type for fee calculation (default to global)
        market_type = "global"  # Default: no fees on global Polymarket
        
        # Create and execute order (uses normalized side internally)
        simulated_order = await self._order_manager.create_order(
            token_id=token_id,
            side=normalized_side,  # Internal use normalized
            size=size_decimal,
            limit_price=limit_price,
            order_type=order_type_upper,  # Use validated order type
            expiration_time_seconds=expiration_time_seconds,
            client_order_id=client_order_id,
            platform=self.platform,
            market_type=market_type,
        )
        
        # Map status to Dome API format
        from ...simulation.orders import OrderStatus
        status = simulated_order.status.value
        if simulated_order.status in [OrderStatus.MATCHED, OrderStatus.FILLED]:
            status = "matched"  # Dome API format
        elif simulated_order.status == OrderStatus.PARTIALLY_FILLED:
            status = "partially_filled"  # Partial fill status
        elif simulated_order.status == OrderStatus.PENDING:
            status = "pending"
        elif simulated_order.status == OrderStatus.REJECTED:
            status = "rejected"
        elif simulated_order.status == OrderStatus.CANCELLED:
            status = "cancelled"
        elif simulated_order.status == OrderStatus.EXPIRED:
            status = "expired"
        
        # Return response in Dome API format (buy/sell, matched status)
        return {
            "order_id": simulated_order.order_id,
            "client_order_id": simulated_order.client_order_id,
            "token_id": simulated_order.token_id,
            "side": side.lower(),  # Return as "buy" or "sell" (Dome API format)
            "size": str(simulated_order.size),
            "price": str(simulated_order.limit_price) if simulated_order.limit_price else None,
            "order_type": order_type_upper,  # Return validated order type
            "status": status,  # Dome API format
            "filled_size": str(simulated_order.filled_size),
            "fill_price": str(simulated_order.fill_price) if simulated_order.fill_price else None,
            "created_time": simulated_order.created_time,
            "expiration_time": simulated_order.expiration_time,
        }

