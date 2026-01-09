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
    fee: Decimal = Decimal(0)  # Transaction fee paid

    @property
    def value(self) -> Decimal:
        return self.quantity * self.price
    
    @property
    def net_value(self) -> Decimal:
        """Trade value after fees."""
        if self.side == 'buy':
            return self.value + self.fee  # Buy: value + fee
        else:
            return self.value - self.fee  # Sell: value - fee


@dataclass
class BacktestResult:
    initial_cash: Decimal
    final_value: Decimal
    equity_curve: List[Tuple[int, Decimal]] = field(default_factory=list)
    trades: List[Trade] = field(default_factory=list)
    total_fees_paid: Decimal = Decimal(0)
    total_interest_earned: Decimal = Decimal(0)

    @property
    def total_return(self) -> Decimal:
        return self.final_value - self.initial_cash

    @property
    def total_return_pct(self) -> float:
        if self.initial_cash == 0:
            return 0.0
        return float(self.total_return / self.initial_cash) * 100
    
    @property
    def net_return_after_fees(self) -> Decimal:
        """Return after accounting for fees (but including interest)."""
        return self.total_return - self.total_fees_paid + self.total_interest_earned
    
    @property
    def net_return_after_fees_pct(self) -> float:
        """Return percentage after fees (but including interest)."""
        if self.initial_cash == 0:
            return 0.0
        return float(self.net_return_after_fees / self.initial_cash) * 100

