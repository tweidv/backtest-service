"""Interest accrual calculation for Kalshi accounts."""

from decimal import Decimal
from typing import Optional


class InterestAccrual:
    """
    Tracks and calculates interest accrual for Kalshi accounts.
    
    Interest accrues daily on:
    - Cash balances
    - End-of-day value of open positions (net portfolio value)
    
    As of 2025, Kalshi offers 4.00% APY (variable rate).
    Interest accrues daily and is paid monthly.
    
    Eligibility:
    - Minimum balance of $250
    - Account funded through Kalshi Klear
    """
    
    def __init__(
        self,
        apy: Decimal = Decimal("0.04"),  # 4% APY
        min_balance: Decimal = Decimal("250"),  # $250 minimum
        enabled: bool = True
    ):
        self.apy = apy
        self.min_balance = min_balance
        self.enabled = enabled
        self.daily_rate = apy / Decimal("365")  # Daily interest rate
        self.accrued_interest: Decimal = Decimal(0)
        self.last_accrual_date: Optional[int] = None  # Unix timestamp
        self.total_interest_paid: Decimal = Decimal(0)
    
    def calculate_daily_interest(
        self,
        cash_balance: Decimal,
        positions_value: Decimal,
        current_timestamp: int
    ) -> Decimal:
        """
        Calculate interest for one day.
        
        Args:
            cash_balance: Available cash
            positions_value: End-of-day value of all open positions
            current_timestamp: Current time (Unix seconds)
        
        Returns:
            Interest accrued for this day
        """
        if not self.enabled:
            return Decimal(0)
        
        # Net portfolio value
        net_value = cash_balance + positions_value
        
        # Check minimum balance requirement
        if net_value < self.min_balance:
            return Decimal(0)
        
        # Calculate daily interest: net_value * daily_rate
        daily_interest = net_value * self.daily_rate
        
        return daily_interest
    
    def accrue_interest(
        self,
        cash_balance: Decimal,
        positions_value: Decimal,
        current_timestamp: int
    ) -> Decimal:
        """
        Accrue interest for the current day and add to total.
        
        Args:
            cash_balance: Available cash
            positions_value: End-of-day value of all open positions
            current_timestamp: Current time (Unix seconds)
        
        Returns:
            Interest accrued today
        """
        daily_interest = self.calculate_daily_interest(
            cash_balance, positions_value, current_timestamp
        )
        
        self.accrued_interest += daily_interest
        self.last_accrual_date = current_timestamp
        
        return daily_interest
    
    def apply_monthly_interest(self) -> Decimal:
        """
        Apply accrued interest (monthly payout).
        Resets accrued_interest to zero.
        
        Returns:
            Total interest to be paid
        """
        interest_to_pay = self.accrued_interest
        self.total_interest_paid += interest_to_pay
        self.accrued_interest = Decimal(0)
        return interest_to_pay

