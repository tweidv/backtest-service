"""Polymarket native SDK backtest client.

Drop-in replacement for py-clob-client.ClobClient that simulates trades.
"""

from decimal import Decimal
from typing import Optional, Dict, Any
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..simulation.clock import SimulationClock
    from ..simulation.portfolio import Portfolio


class PolymarketBacktestClient:
    """
    Drop-in replacement for py-clob-client ClobClient that simulates trades.
    
    Matches the py-clob-client API signature for create_order().
    
    Usage:
        # Live
        from py_clob_client import ClobClient
        client = ClobClient(api_key="...", ...)
        order = await client.create_order(...)
        
        # Backtest - just swap import!
        from backtest_service.native import PolymarketBacktestClient
        client = PolymarketBacktestClient({
            "dome_api_key": "...",  # For historical data via Dome
            "start_time": 1729800000,
            "end_time": 1729886400,
            "initial_cash": 10000,
        })
        
        # Same code works! ✅
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
                    super().__init__("polymarket", dome_client, clock, portfolio)
                    self._real_api = dome_client.polymarket
            
            wrapper = WrapperAPI(self._dome_client, self._clock, self._portfolio)
            self._orderbook_sim = OrderbookSimulator(wrapper)
            self._order_manager = OrderManager(self._clock, self._portfolio, self._orderbook_sim)
            
        else:
            # Live mode - delegate to real py-clob-client
            try:
                from py_clob_client import ClobClient
                polymarket_api_key = config.get("polymarket_api_key") or config.get("polymarketApiKey")
                if not polymarket_api_key:
                    raise ValueError("polymarket_api_key is required for live mode")
                self._real_client = ClobClient(api_key=polymarket_api_key)
            except ImportError:
                raise ImportError(
                    "py-clob-client is required for live mode. "
                    "Install with: pip install py-clob-client"
                )
        
        # Expose portfolio for strategy access
        self.portfolio = self._portfolio if self.mode == "backtest" else None
    
    async def create_order(
        self,
        token_id: str,
        side: str,
        size: str,
        price: str,
        order_type: str = "GTC",
        expiration_time_seconds: Optional[int] = None,
        post_only: bool = False,
        client_order_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Create an order - matches py-clob-client API signature exactly.
        
        Args:
            token_id: Condition token ID (required)
            side: "YES" or "NO" (required)
            size: Order size as string in base units (required)
            price: Limit price as string (0-1) (required for limit orders)
            order_type: "MARKET", "FOK", "GTC", or "GTD" (default: "GTC")
            expiration_time_seconds: Required for GTD orders
            post_only: If True, order only rests (no immediate match)
            client_order_id: Optional custom order ID
        
        Returns:
            Order response dict matching py-clob-client structure
        
        Example:
            order = await client.create_order(
                token_id="0x123...",
                side="YES",
                size="1000000000",
                price="0.65",
                order_type="GTC"
            )
        """
        if self.mode == "backtest":
            # Simulate order
            simulated_order = await self._order_manager.create_order(
                token_id=token_id,
                side=side.upper(),
                size=Decimal(size),
                limit_price=Decimal(price) if price else None,
                order_type=order_type,
                expiration_time_seconds=expiration_time_seconds,
                client_order_id=client_order_id,
                platform="polymarket",
            )
            
            # Return response matching py-clob-client structure
            return {
                "order_id": simulated_order.order_id,
                "client_order_id": simulated_order.client_order_id,
                "token_id": simulated_order.token_id,
                "side": simulated_order.side,
                "size": str(simulated_order.size),
                "price": str(simulated_order.limit_price) if simulated_order.limit_price else None,
                "order_type": simulated_order.order_type,
                "status": simulated_order.status.value,
                "filled_size": str(simulated_order.filled_size),
                "fill_price": str(simulated_order.fill_price) if simulated_order.fill_price else None,
                "created_time": simulated_order.created_time,
                "expiration_time": simulated_order.expiration_time,
            }
        else:
            # Live - delegate to real client
            return await self._real_client.create_order(
                token_id=token_id,
                side=side,
                size=size,
                price=price,
                order_type=order_type,
                expiration_time_seconds=expiration_time_seconds,
                post_only=post_only,
                client_order_id=client_order_id,
            )
    
    async def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """
        Cancel an order - matches py-clob-client API.
        
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
        Get current positions - matches py-clob-client API.
        
        Returns:
            Positions dict
        """
        if self.mode == "backtest":
            return {
                "positions": {
                    token_id: {
                        "token_id": token_id,
                        "quantity": str(qty),
                        "platform": "polymarket"
                    }
                    for token_id, qty in self._portfolio.positions.items()
                }
            }
        else:
            # Live - delegate to real client
            return await self._real_client.get_positions()
    
    async def get_balance(self) -> Dict[str, Any]:
        """
        Get account balance - matches py-clob-client API.
        
        Returns:
            Balance dict
        """
        if self.mode == "backtest":
            return {
                "balance": str(self._portfolio.cash),
                "available": str(self._portfolio.cash),
            }
        else:
            # Live - delegate to real client
            return await self._real_client.get_balance()

