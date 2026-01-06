from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Tuple


@dataclass
class Trade:
    timestamp: int
    platform: str  # 'polymarket' or 'kalshi'
    token_id: str
    side: str  # 'buy' or 'sell'
    quantity: Decimal
    price: Decimal

    @property
    def value(self) -> Decimal:
        return self.quantity * self.price


@dataclass
class BacktestResult:
    initial_cash: Decimal
    final_value: Decimal
    equity_curve: List[Tuple[int, Decimal]] = field(default_factory=list)
    trades: List[Trade] = field(default_factory=list)

    @property
    def total_return(self) -> Decimal:
        return self.final_value - self.initial_cash

    @property
    def total_return_pct(self) -> float:
        if self.initial_cash == 0:
            return 0.0
        return float(self.total_return / self.initial_cash) * 100

