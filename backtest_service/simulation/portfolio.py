from decimal import Decimal
from typing import Dict, List, Optional, Literal
from dataclasses import dataclass
from ..models.result import Trade


@dataclass
class Position:
    """Represents a position with quantity, average price, and cost basis."""
    token_id: str
    quantity: Decimal
    avg_price: Decimal  # Average entry price (excluding fees)
    cost_basis: Decimal  # Total cost including fees
    platform: str = "polymarket"  # Track platform for reference
    
    @property
    def value(self) -> Decimal:
        """Current position value (quantity * avg_price)."""
        return self.quantity * self.avg_price


class Portfolio:
    def __init__(
        self,
        initial_cash: Decimal,
        enable_fees: bool = True,
        enable_interest: bool = False,  # Kalshi only
        interest_apy: Decimal = Decimal("0.04")
    ):
        self.cash = Decimal(initial_cash)
        self.positions: Dict[str, Decimal] = {}  # token_id -> quantity (backward compatibility)
        self._position_details: Dict[str, Position] = {}  # token_id -> Position (enhanced tracking)
        self.trades: List[Trade] = []
        
        # Fee tracking
        self.enable_fees = enable_fees
        self.total_fees_paid: Decimal = Decimal(0)
        
        # Interest tracking (Kalshi)
        self.enable_interest = enable_interest
        if enable_interest:
            from .interest import InterestAccrual
            self.interest_accrual = InterestAccrual(apy=interest_apy)
        else:
            self.interest_accrual = None

    def buy(
        self,
        platform: str,
        token_id: str,
        quantity: Decimal,
        price: Decimal,
        timestamp: int,
        order_type: str = "taker",  # "maker" or "taker"
        market_type: str = "global"  # For Polymarket: "global", "us", "crypto_15min"
    ):
        cost = quantity * price
        
        # Calculate and apply fees
        fee = Decimal(0)
        if self.enable_fees:
            if platform == "kalshi":
                from .fees import calculate_kalshi_fee
                fee = calculate_kalshi_fee(quantity, price)
            elif platform == "polymarket":
                from .fees import calculate_polymarket_fee
                fee = calculate_polymarket_fee(cost, market_type, order_type)
        
        total_cost = cost + fee
        
        if total_cost > self.cash:
            raise ValueError(
                f"Insufficient cash: need {total_cost} (cost: {cost}, fee: {fee}), "
                f"have {self.cash}"
            )
        
        self.cash -= total_cost
        self.total_fees_paid += fee
        
        # Update positions (backward compatibility)
        self.positions[token_id] = self.positions.get(token_id, Decimal(0)) + quantity
        
        # Update position details with cost basis tracking
        if token_id in self._position_details:
            # Existing position - update average price and cost basis
            pos = self._position_details[token_id]
            old_value = pos.quantity * pos.avg_price
            new_value = quantity * price
            total_quantity = pos.quantity + quantity
            # Weighted average price
            pos.avg_price = (old_value + new_value) / total_quantity
            pos.cost_basis += total_cost  # Add total cost (including fees)
            pos.quantity = total_quantity
        else:
            # New position
            self._position_details[token_id] = Position(
                token_id=token_id,
                quantity=quantity,
                avg_price=price,
                cost_basis=total_cost,  # Total cost including fees
                platform=platform
            )
        
        self.trades.append(Trade(
            timestamp=timestamp,
            platform=platform,
            token_id=token_id,
            side='buy',
            quantity=quantity,
            price=price,
            fee=fee,
        ))

    def sell(
        self,
        platform: str,
        token_id: str,
        quantity: Decimal,
        price: Decimal,
        timestamp: int,
        order_type: str = "taker",  # "maker" or "taker"
        market_type: str = "global"  # For Polymarket: "global", "us", "crypto_15min"
    ):
        held = self.positions.get(token_id, Decimal(0))
        if quantity > held:
            raise ValueError(f"Insufficient position: need {quantity}, have {held}")
        
        proceeds = quantity * price
        
        # Calculate and apply fees
        fee = Decimal(0)
        if self.enable_fees:
            if platform == "kalshi":
                from .fees import calculate_kalshi_fee
                fee = calculate_kalshi_fee(quantity, price)
            elif platform == "polymarket":
                from .fees import calculate_polymarket_fee
                fee = calculate_polymarket_fee(proceeds, market_type, order_type)
        
        net_proceeds = proceeds - fee
        
        self.cash += net_proceeds
        self.total_fees_paid += fee
        
        # Update positions (backward compatibility)
        self.positions[token_id] = held - quantity
        if self.positions[token_id] == 0:
            del self.positions[token_id]
        
        # Update position details - reduce cost basis proportionally
        if token_id in self._position_details:
            pos = self._position_details[token_id]
            if pos.quantity > 0:
                # Reduce cost basis proportionally
                cost_basis_sold = (pos.cost_basis * quantity) / pos.quantity
                pos.cost_basis -= cost_basis_sold
                pos.quantity -= quantity
                
                if pos.quantity <= 0:
                    # Position closed
                    del self._position_details[token_id]
            else:
                # Position already closed (shouldn't happen, but handle gracefully)
                del self._position_details[token_id]
        
        self.trades.append(Trade(
            timestamp=timestamp,
            platform=platform,
            token_id=token_id,
            side='sell',
            quantity=quantity,
            price=price,
            fee=fee,
        ))

    def get_value(self, prices: Dict[str, Decimal]) -> Decimal:
        """Total portfolio value = cash + sum(position * price)"""
        positions_value = sum(
            qty * prices.get(token_id, Decimal(0))
            for token_id, qty in self.positions.items()
        )
        return self.cash + positions_value
    
    def get_position(self, token_id: str) -> Optional[Position]:
        """
        Get position details for a token.
        
        Returns:
            Position object with quantity, avg_price, cost_basis, or None if no position
        """
        return self._position_details.get(token_id)
    
    def get_position_pnl(self, token_id: str, current_price: Decimal) -> Optional[Decimal]:
        """
        Calculate unrealized P&L for a position.
        
        Args:
            token_id: Token ID
            current_price: Current market price
            
        Returns:
            Unrealized P&L (current_value - cost_basis), or None if no position
        """
        pos = self.get_position(token_id)
        if pos is None:
            return None
        
        current_value = pos.quantity * current_price
        return current_value - pos.cost_basis
    
    @property
    def total_value(self) -> Decimal:
        """
        Total portfolio value (requires prices to be provided via get_value()).
        This property is a placeholder - use get_value(prices) for actual calculation.
        """
        # This is a convenience property, but actual calculation needs prices
        # We'll implement this properly in DomeBacktestClient
        return self.cash

