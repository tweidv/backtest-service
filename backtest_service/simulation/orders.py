"""Order management and simulation for backtesting."""

from decimal import Decimal
from dataclasses import dataclass
from typing import Optional, List
from enum import Enum


class OrderStatus(Enum):
    """Order status enumeration."""
    PENDING = "pending"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    REJECTED = "rejected"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


@dataclass
class SimulatedOrder:
    """Represents a simulated order."""
    order_id: str
    token_id: str  # Token ID (Polymarket) or ticker (Kalshi)
    side: str  # "YES", "NO", "yes", "no", "BUY", "SELL"
    size: Decimal  # Order size
    limit_price: Optional[Decimal]  # None for market orders
    order_type: str  # "MARKET", "LIMIT", "FOK", "GTC", "GTD"
    status: OrderStatus
    filled_size: Decimal
    fill_price: Optional[Decimal]
    created_time: int
    expiration_time: Optional[int]
    client_order_id: Optional[str] = None
    platform: str = "polymarket"  # Track platform for fee calculation
    market_type: str = "global"  # For Polymarket: "global", "us", "crypto_15min"
    was_pending: bool = False  # True if order rested on book (maker), False if filled immediately (taker)
    
    def to_dict(self) -> dict:
        """Convert to dictionary matching real API response structure."""
        return {
            "order_id": self.order_id,
            "token_id": self.token_id,
            "side": self.side,
            "size": str(self.size),
            "limit_price": str(self.limit_price) if self.limit_price else None,
            "order_type": self.order_type,
            "status": self.status.value,
            "filled_size": str(self.filled_size),
            "fill_price": str(self.fill_price) if self.fill_price else None,
            "created_time": self.created_time,
            "expiration_time": self.expiration_time,
            "client_order_id": self.client_order_id,
        }


class OrderManager:
    """Manages pending orders and order execution."""
    
    def __init__(self, clock, portfolio, orderbook_simulator):
        self._clock = clock
        self._portfolio = portfolio
        self._orderbook_sim = orderbook_simulator
        self._pending_orders: List[SimulatedOrder] = []
        self._order_counter = 0
    
    def _generate_order_id(self) -> str:
        """Generate unique order ID."""
        self._order_counter += 1
        return f"order_{self._clock.current_time}_{self._order_counter}"
    
    async def create_order(
        self,
        token_id: str,
        side: str,
        size: Decimal,
        limit_price: Optional[Decimal] = None,
        order_type: str = "GTC",
        expiration_time_seconds: Optional[int] = None,
        client_order_id: Optional[str] = None,
        platform: str = "polymarket",
        market_type: str = "global",  # For Polymarket fee calculation
    ) -> SimulatedOrder:
        """
        Create and attempt to execute an order.
        
        Returns:
            SimulatedOrder with status and fill information
        """
        order_id = client_order_id or self._generate_order_id()
        
        # Validate order type
        valid_types = ["MARKET", "LIMIT", "FOK", "GTC", "GTD"]
        if order_type not in valid_types:
            raise ValueError(f"order_type must be one of {valid_types}, got: {order_type}")
        
        # Validate GTD requires expiration
        if order_type == "GTD" and expiration_time_seconds is None:
            raise ValueError("expiration_time_seconds is required for GTD orders")
        
        # Determine if this is a maker or taker order
        # Maker = limit order that doesn't fill immediately (rests on book)
        # Taker = market order or limit order that fills immediately
        # We'll determine this after trying to fill
        
        # Create order object
        order = SimulatedOrder(
            order_id=order_id,
            token_id=token_id,
            side=side,
            size=size,
            limit_price=limit_price,
            order_type=order_type,
            status=OrderStatus.PENDING,
            filled_size=Decimal(0),
            fill_price=None,
            created_time=self._clock.current_time,
            expiration_time=expiration_time_seconds,
            client_order_id=client_order_id,
            platform=platform,
            market_type=market_type,
        )
        
        # Attempt to fill immediately
        result = await self._try_fill_order(order, platform)
        
        # If not filled and is a limit order that can persist, add to pending
        # This means it will be a maker order (provides liquidity)
        if (result.status == OrderStatus.PENDING and 
            order_type in ["GTC", "GTD"] and 
            limit_price is not None):
            result.was_pending = True  # Mark as maker order
            self._pending_orders.append(result)
        else:
            # Filled immediately = taker order (takes liquidity)
            result.was_pending = False
        
        return result
    
    async def _try_fill_order(self, order: SimulatedOrder, platform: str) -> SimulatedOrder:
        """Try to fill an order based on orderbook."""
        # Get current orderbook
        orderbook = await self._orderbook_sim.get_historical_orderbook(
            order.token_id,
            self._clock.current_time
        )
        
        # Handle market orders
        if order.order_type == "MARKET" or order.limit_price is None:
            fill_price = self._orderbook_sim.get_market_price(
                orderbook, order.side, platform
            )
            
            if fill_price is None:
                # No liquidity - reject
                order.status = OrderStatus.REJECTED
                return order
            
            # Market order fills immediately at best price
            return await self._execute_fill(order, order.size, fill_price, platform)
        
        # Handle limit orders
        can_fill = self._orderbook_sim.can_fill_at_price(
            orderbook, order.side, order.limit_price, order.size, platform
        )
        
        if order.order_type == "FOK":
            # Fill-or-Kill: fill completely or reject
            if can_fill:
                return await self._execute_fill(order, order.size, order.limit_price, platform)
            else:
                order.status = OrderStatus.REJECTED
                return order
        
        elif order.order_type in ["GTC", "GTD"]:
            # Good-Till-Cancel/Date: fill if marketable, otherwise queue
            if can_fill:
                # Fills immediately = taker order (takes liquidity)
                # was_pending is already False (default)
                return await self._execute_fill(order, order.size, order.limit_price, platform)
            else:
                # Not marketable - will rest on book = maker order (provides liquidity)
                # was_pending will be set to True when added to pending_orders
                order.status = OrderStatus.PENDING
                return order
        
        # Default: reject unknown types
        order.status = OrderStatus.REJECTED
        return order
    
    async def _execute_fill(
        self, 
        order: SimulatedOrder, 
        fill_size: Decimal, 
        fill_price: Decimal,
        platform: str
    ) -> SimulatedOrder:
        """Execute a fill and update portfolio."""
        side_lower = order.side.lower()
        
        # Determine if this is a buy or sell
        is_buy = side_lower in ["yes", "buy"]
        
        # For Kalshi, use composite key (ticker:side) to track YES/NO separately
        # For Polymarket, token_id already uniquely identifies the side
        if platform == "kalshi":
            # Kalshi positions need side tracking: use "ticker:YES" or "ticker:NO"
            position_key = f"{order.token_id}:{order.side.upper()}"
        else:
            position_key = order.token_id
        
        # Determine if this is a maker or taker order for fee calculation
        # - Maker = limit order that rested on book (was pending) and now gets filled
        # - Taker = market order OR limit order that filled immediately (crossed spread)
        # Market orders are always takers
        if order.order_type == "MARKET" or order.limit_price is None:
            order_type_for_fees = "taker"  # Market orders always take liquidity
        elif order.was_pending:
            order_type_for_fees = "maker"  # Was pending = provided liquidity
        else:
            order_type_for_fees = "taker"  # Filled immediately = took liquidity
        
        try:
            if is_buy:
                # Buying: reduce cash, increase position
                self._portfolio.buy(
                    platform=platform,
                    token_id=position_key,
                    quantity=fill_size,
                    price=fill_price,
                    timestamp=self._clock.current_time,
                    order_type=order_type_for_fees,
                    market_type=order.market_type,
                )
            else:
                # Selling: increase cash, decrease position
                self._portfolio.sell(
                    platform=platform,
                    token_id=position_key,
                    quantity=fill_size,
                    price=fill_price,
                    timestamp=self._clock.current_time,
                    order_type=order_type_for_fees,
                    market_type=order.market_type,
                )
            
            # Update order
            order.filled_size = fill_size
            order.fill_price = fill_price
            
            if fill_size == order.size:
                order.status = OrderStatus.FILLED
            else:
                order.status = OrderStatus.PARTIALLY_FILLED
            
        except ValueError as e:
            # Insufficient cash or position
            order.status = OrderStatus.REJECTED
            order.fill_price = None
            order.filled_size = Decimal(0)
        
        return order
    
    async def process_pending_orders(self, platform: str = "polymarket"):
        """Check and fill pending limit orders."""
        remaining_orders = []
        
        for order in self._pending_orders:
            # Check expiration
            if order.order_type == "GTD" and order.expiration_time:
                if self._clock.current_time > order.expiration_time:
                    order.status = OrderStatus.EXPIRED
                    continue  # Don't add back to pending
            
            # Try to fill
            result = await self._try_fill_order(order, platform)
            
            if result.status == OrderStatus.PENDING:
                # Still pending - keep in queue
                remaining_orders.append(result)
            elif result.status == OrderStatus.FILLED:
                # Fully filled - remove from pending
                pass
            elif result.status == OrderStatus.PARTIALLY_FILLED:
                # Partially filled - update size and keep if still pending
                order.size -= result.filled_size
                if order.size > 0:
                    remaining_orders.append(order)
        
        self._pending_orders = remaining_orders
    
    def cancel_order(self, order_id: str) -> Optional[SimulatedOrder]:
        """Cancel a pending order."""
        for i, order in enumerate(self._pending_orders):
            if order.order_id == order_id:
                order.status = OrderStatus.CANCELLED
                self._pending_orders.pop(i)
                return order
        return None
    
    def get_pending_orders(self) -> List[SimulatedOrder]:
        """Get all pending orders."""
        return self._pending_orders.copy()

