from decimal import Decimal
from typing import Dict, List, Optional, Literal
from ..models.result import Trade


class Portfolio:
    def __init__(
        self,
        initial_cash: Decimal,
        enable_fees: bool = True,
        enable_interest: bool = False,  # Kalshi only
        interest_apy: Decimal = Decimal("0.04")
    ):
        self.cash = Decimal(initial_cash)
        self.positions: Dict[str, Decimal] = {}  # token_id -> quantity
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
        self.positions[token_id] = self.positions.get(token_id, Decimal(0)) + quantity
        
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
        self.positions[token_id] = held - quantity
        if self.positions[token_id] == 0:
            del self.positions[token_id]
        
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

