from decimal import Decimal
from typing import Dict, List
from ..models.result import Trade


class Portfolio:
    def __init__(self, initial_cash: Decimal):
        self.cash = Decimal(initial_cash)
        self.positions: Dict[str, Decimal] = {}  # token_id -> quantity
        self.trades: List[Trade] = []

    def buy(self, platform: str, token_id: str, quantity: Decimal, price: Decimal, timestamp: int):
        cost = quantity * price
        if cost > self.cash:
            raise ValueError(f"Insufficient cash: need {cost}, have {self.cash}")
        
        self.cash -= cost
        self.positions[token_id] = self.positions.get(token_id, Decimal(0)) + quantity
        self.trades.append(Trade(
            timestamp=timestamp,
            platform=platform,
            token_id=token_id,
            side='buy',
            quantity=quantity,
            price=price,
        ))

    def sell(self, platform: str, token_id: str, quantity: Decimal, price: Decimal, timestamp: int):
        held = self.positions.get(token_id, Decimal(0))
        if quantity > held:
            raise ValueError(f"Insufficient position: need {quantity}, have {held}")
        
        self.cash += quantity * price
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
        ))

    def get_value(self, prices: Dict[str, Decimal]) -> Decimal:
        """Total portfolio value = cash + sum(position * price)"""
        positions_value = sum(
            qty * prices.get(token_id, Decimal(0))
            for token_id, qty in self.positions.items()
        )
        return self.cash + positions_value

