"""
Example backtest usage.

Run with:
    set DOME_API_KEY=your-api-key
    python example.py
"""
import asyncio
import os
from decimal import Decimal

from backtest_service import BacktestRunner


# Trump 2024 Election Market - YES token
TOKEN_ID = "21742633143463906290569050155826241533067272736897614950488156847949938836455"


async def simple_strategy(dome, portfolio):
    """Buy low, sell high."""
    try:
        price_data = await dome.polymarket.get_market_price({"token_id": TOKEN_ID})
        price = Decimal(str(price_data.price))
        
        # Buy if cheap and we have cash
        if price < Decimal("0.55") and portfolio.cash > 500:
            qty = (Decimal("500") / price).quantize(Decimal("1"))
            dome.polymarket.buy(TOKEN_ID, qty, price)
            print(f"  BUY {qty} @ {price:.4f}")
        
        # Sell if expensive and we have position
        elif price > Decimal("0.65") and TOKEN_ID in portfolio.positions:
            qty = portfolio.positions[TOKEN_ID]
            dome.polymarket.sell(TOKEN_ID, qty, price)
            print(f"  SELL {qty} @ {price:.4f}")
        
        else:
            print(f"  HOLD @ {price:.4f}")
    
    except Exception as e:
        print(f"  Error: {e}")


async def get_prices(dome):
    """Get prices for portfolio valuation."""
    try:
        data = await dome.polymarket.get_market_price({"token_id": TOKEN_ID})
        return {TOKEN_ID: Decimal(str(data.price))}
    except:
        return {}


async def main():
    api_key = os.environ.get("DOME_API_KEY")
    if not api_key:
        print("Set DOME_API_KEY environment variable")
        return
    
    print("=" * 50)
    print("BACKTEST EXAMPLE")
    print("=" * 50)
    
    # 24-hour backtest during election week
    runner = BacktestRunner(
        api_key=api_key,
        start_time=1729800000,  # Oct 24, 2024
        end_time=1729886400,    # Oct 25, 2024
        step=3600,              # 1 hour intervals
        initial_cash=Decimal("10000"),
    )
    
    print(f"Period: Oct 24-25, 2024")
    print(f"Strategy: Buy < $0.55, Sell > $0.65")
    print("-" * 50)
    
    result = await runner.run(simple_strategy, get_prices)
    
    print("-" * 50)
    print(f"Initial:  ${result.initial_cash}")
    print(f"Final:    ${result.final_value:.2f}")
    print(f"Return:   {result.total_return_pct:+.2f}%")
    print(f"Trades:   {len(result.trades)}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())
