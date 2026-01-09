"""Kalshi native SDK backtest client.

Drop-in replacement for kalshi.KalshiClient that simulates trades.
"""

from decimal import Decimal
from typing import Optional, Dict, Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..simulation.clock import SimulationClock
    from ..simulation.portfolio import Portfolio


class KalshiBacktestClient:
    """
    Drop-in replacement for kalshi KalshiClient that simulates trades.
    
    Matches the kalshi SDK API signature for create_order().
    
    Usage:
        # Live
        from kalshi import KalshiClient
        client = KalshiClient(api_key="...", ...)
        order = await client.create_order(...)
        
        # Backtest - just swap import!
        from emulo.native import KalshiBacktestClient
        client = KalshiBacktestClient({
            "dome_api_key": "...",  # For historical data via Dome
            "start_time": 1729800000,
            "end_time": 1729886400,
            "initial_cash": 10000,
        })
        
        # Same code works!
        order = await client.create_order(...)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize backtest client.
        
        Args:
            config: Configuration dict with:
                - dome_api_key: Dome API key for historical data
                - start_time: Backtest start time (Unix seconds)
                - end_time: Backtest end time (Unix seconds)
                - initial_cash: Starting capital (default: 10000)
                - mode: "backtest" or "live" (default: "backtest")
        """
        from dome_api_sdk import DomeClient
        from ..simulation.clock import SimulationClock
        from ..simulation.portfolio import Portfolio
        
        import os
        
        self.mode = config.get("mode", "backtest")
        self.dome_api_key = config.get("dome_api_key") or config.get("domeApiKey")
        # Auto-load from environment if not provided in config
        if not self.dome_api_key:
            self.dome_api_key = os.environ.get("DOME_API_KEY")
        if not self.dome_api_key:
            raise ValueError(
                "dome_api_key is required in config or set DOME_API_KEY environment variable."
            )
        
        if self.mode == "backtest":
            self.start_time = config.get("start_time") or config.get("startTime")
            self.end_time = config.get("end_time") or config.get("endTime")
            if self.start_time is None or self.end_time is None:
                raise ValueError("start_time and end_time are required for backtest mode")
            
            self._clock = SimulationClock(self.start_time)
            self._portfolio = Portfolio(Decimal(str(config.get("initial_cash", 10000))))
            self._dome_client = DomeClient({"api_key": self.dome_api_key})
            
            # Initialize order simulation
            from ..simulation.orderbook import OrderbookSimulator
            from ..simulation.orders import OrderManager
            from ..api.base_api import BasePlatformAPI
            
            # Create a wrapper API object for orderbook simulator
            class WrapperAPI(BasePlatformAPI):
                def __init__(self, dome_client, clock, portfolio):
                    super().__init__("kalshi", dome_client, clock, portfolio)
                    self._real_api = dome_client.kalshi
            
            wrapper = WrapperAPI(self._dome_client, self._clock, self._portfolio)
            self._orderbook_sim = OrderbookSimulator(wrapper)
            self._order_manager = OrderManager(self._clock, self._portfolio, self._orderbook_sim)
            
        else:
            # Live mode - delegate to real kalshi SDK
            try:
                from kalshi import KalshiClient
                kalshi_api_key = config.get("kalshi_api_key") or config.get("kalshiApiKey")
                if not kalshi_api_key:
                    raise ValueError("kalshi_api_key is required for live mode")
                # Note: Kalshi SDK might require additional initialization
                self._real_client = KalshiClient(api_key=kalshi_api_key)
            except ImportError:
                raise ImportError(
                    "kalshi SDK is required for live mode. "
                    "Install with: pip install kalshi"
                )
        
        # Expose portfolio for strategy access
        self.portfolio = self._portfolio if self.mode == "backtest" else None
    
    async def create_order(
        self,
        ticker: str,
        side: str,
        action: str,
        count: int,
        order_type: str = "limit",
        yes_price: Optional[int] = None,
        no_price: Optional[int] = None,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an order - matches kalshi SDK API signature exactly.
        
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
            Order response dict matching kalshi SDK structure
        
        Example:
            order = await client.create_order(
                ticker="KXNFLGAME-25AUG16ARIDEN-ARI",
                side="yes",
                action="buy",
                count=100,
                order_type="limit",
                yes_price=75  # cents
            )
        """
        if self.mode == "backtest":
            # Validate and convert price
            if order_type == "limit":
                if side.lower() == "yes" and yes_price is None:
                    raise ValueError("yes_price is required for YES side limit orders")
                if side.lower() == "no" and no_price is None:
                    raise ValueError("no_price is required for NO side limit orders")
                
                if side.lower() == "yes":
                    limit_price = Decimal(yes_price) / Decimal(100)  # Convert cents to 0-1
                else:
                    limit_price = Decimal(no_price) / Decimal(100)  # Convert cents to 0-1
            else:
                limit_price = None
            
            # Map kalshi order types to Dome API format
            # kalshi uses "market", Dome uses "FOK"
            mapped_order_type = "FOK" if order_type == "market" else "GTC"
            
            # Normalize side - kalshi uses yes/no, which normalize_side accepts
            from ..simulation.orders import normalize_side
            normalized_side = normalize_side(side)
            
            # Simulate order
            simulated_order = await self._order_manager.create_order(
                token_id=ticker,
                side=normalized_side,  # Use normalized side
                size=Decimal(count),
                limit_price=limit_price,
                order_type=mapped_order_type,  # Use mapped order type
                expiration_time_seconds=None,
                client_order_id=client_order_id,
                platform="kalshi",
            )
            
            # Return response matching kalshi SDK structure
            fill_price_cents = int(simulated_order.fill_price * 100) if simulated_order.fill_price else None
            
            # Kalshi SDK expects status in their format - keep original status mapping
            status = simulated_order.status.value
            # Kalshi SDK might expect different status format, but we'll use our standard
            
            return {
                "order_id": simulated_order.order_id,
                "client_order_id": simulated_order.client_order_id,
                "ticker": simulated_order.token_id,
                "side": side.lower(),  # Return as yes/no (kalshi format)
                "action": action.lower(),
                "count": int(simulated_order.size),
                "type": order_type,  # Return original order_type (limit/market)
                "yes_price": yes_price,
                "no_price": no_price,
                "status": status,  # Keep status as-is (kalshi SDK format)
                "filled_count": int(simulated_order.filled_size),
                "fill_price": fill_price_cents,
                "created_time": simulated_order.created_time,
            }
        else:
            # Live - delegate to real client
            return await self._real_client.create_order(
                ticker=ticker,
                side=side,
                action=action,
                count=count,
                order_type=order_type,
                yes_price=yes_price,
                no_price=no_price,
                client_order_id=client_order_id,
            )
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an order - matches kalshi SDK API.
        
        Args:
            order_id: Order ID to cancel
        
        Returns:
            Cancellation response dict
        """
        if self.mode == "backtest":
            cancelled_order = self._order_manager.cancel_order(order_id)
            if cancelled_order:
                return {
                    "order_id": cancelled_order.order_id,
                    "status": "cancelled",
                }
            else:
                raise ValueError(f"Order {order_id} not found or already filled/cancelled")
        else:
            # Live - delegate to real client
            return await self._real_client.cancel_order(order_id)
    
    async def get_positions(self) -> Dict[str, Any]:
        """
        Get current positions - matches kalshi SDK API.
        
        Returns:
            Positions dict
        """
        if self.mode == "backtest":
            positions_list = []
            for position_key, qty in self._portfolio.positions.items():
                # Parse position key: could be "ticker:YES", "ticker:NO", or just "ticker" (legacy)
                if ":" in position_key:
                    ticker, side = position_key.rsplit(":", 1)
                    positions_list.append({
                        "ticker": ticker,
                        "count": int(qty),
                        "side": side.lower(),
                    })
                else:
                    # Legacy format without side - default to "yes"
                    positions_list.append({
                        "ticker": position_key,
                        "count": int(qty),
                        "side": "yes",
                    })
            
            return {
                "positions": positions_list
            }
        else:
            # Live - delegate to real client
            return await self._real_client.get_positions()
    
    async def get_balance(self) -> Dict[str, Any]:
        """
        Get account balance - matches kalshi SDK API.
        
        Returns:
            Balance dict
        """
        if self.mode == "backtest":
            # Kalshi balance in cents
            balance_cents = int(self._portfolio.cash * 100)
            return {
                "balance": balance_cents,
                "available": balance_cents,
            }
        else:
            # Live - delegate to real client
            return await self._real_client.get_balance()

