"""Transaction fee calculation for Polymarket and Kalshi."""

from decimal import Decimal
from typing import Literal
import math


def calculate_polymarket_fee(
    trade_value: Decimal,
    market_type: Literal["global", "us", "crypto_15min"] = "global",
    order_type: Literal["maker", "taker"] = "taker"
) -> Decimal:
    """
    Calculate Polymarket trading fees.
    
    Args:
        trade_value: Total value of the trade (quantity * price)
        market_type: Type of market (global, us, crypto_15min)
        order_type: Whether order is maker or taker
    
    Returns:
        Fee amount in same currency units as trade_value
    
    Note:
        - Global platform: No fees
        - US market (QCEX): 0.01% taker fee
        - 15-minute crypto markets: Taker fees with maker rebates
    """
    if market_type == "global":
        return Decimal(0)  # No fees on global platform
    elif market_type == "us":
        if order_type == "taker":
            return trade_value * Decimal("0.0001")  # 0.01% taker fee
        else:
            return Decimal(0)  # No maker fee (or rebate)
    elif market_type == "crypto_15min":
        if order_type == "taker":
            # Taker fee on 15-minute crypto markets
            # Exact rate may vary - using placeholder
            return trade_value * Decimal("0.001")  # Example 0.1%
        else:
            # Maker rebate (negative fee)
            return -trade_value * Decimal("0.0005")  # Example 0.05% rebate
    
    return Decimal(0)


def calculate_kalshi_fee(
    contract_count: Decimal,
    contract_price: Decimal
) -> Decimal:
    """
    Calculate Kalshi trading fees using official formula.
    
    Formula: round_up(0.07 × C × P × (1 - P))
    Where C = contracts, P = price in dollars
    
    Args:
        contract_count: Number of contracts (C)
        contract_price: Price per contract in dollars (P), e.g., 0.5 for 50 cents
    
    Returns:
        Fee amount in dollars
    
    Examples:
        - 100 contracts @ $0.50: fee ≈ $1.75
        - Higher fees for extreme probabilities (near $0.01 or $0.99)
        - Lower fees for 50/50 contracts (near $0.50)
    """
    # Ensure contract_price is between 0 and 1
    if contract_price < Decimal(0) or contract_price > Decimal(1):
        raise ValueError(f"Contract price must be between 0 and 1, got {contract_price}")
    
    # Calculate: 0.07 × C × P × (1 - P)
    fee = Decimal("0.07") * contract_count * contract_price * (Decimal(1) - contract_price)
    
    # Round up to nearest cent
    fee_cents = math.ceil(float(fee) * 100)
    return Decimal(fee_cents) / Decimal(100)

