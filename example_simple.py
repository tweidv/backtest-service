"""
Simple example showing the new minimal-effort interface.

This demonstrates how easy it is to convert a live trading strategy to backtesting:
1. Swap the import
2. Add dates to config
3. Call run()
"""
import asyncio
import os
from decimal import Decimal
from datetime import datetime

# Just swap this import!
from backtest_service import DomeBacktestClient
# from dome_api_sdk import DomeClient  # Production version

TOKEN_ID = "21742633143463906290569050155826241533067272736897614950488156847949938836455"


async def my_strategy(dome):
    """
    Your existing strategy - works in both production and backtest!
    Just access portfolio via dome.portfolio instead of a separate parameter.
    """
    try:
        price_data = await dome.polymarket.get_market_price({"token_id": TOKEN_ID})
        price = Decimal(str(price_data.price))
        
        # Buy if cheap and we have cash
        if price < Decimal("0.55") and dome.portfolio.cash > 500:
            qty = (Decimal("500") / price).quantize(Decimal("1"))
            dome.polymarket.buy(TOKEN_ID, qty, price)
            print(f"  BUY {qty} @ {price:.4f}")
        
        # Sell if expensive and we have position
        elif price > Decimal("0.65") and TOKEN_ID in dome.portfolio.positions:
            qty = dome.portfolio.positions[TOKEN_ID]
            dome.polymarket.sell(TOKEN_ID, qty, price)
            print(f"  SELL {qty} @ {price:.4f}")
        
        else:
            print(f"  HOLD @ {price:.4f}")
    
    except Exception as e:
        print(f"  Error: {e}")


async def main():
    api_key = os.environ.get("DOME_API_KEY")
    if not api_key:
        print("Set DOME_API_KEY environment variable")
        return
    
    print("=" * 50)
    print("SIMPLE BACKTEST - NEW INTERFACE")
    print("=" * 50)
    
    # Convert dates to timestamps
    start_time = int(datetime(2024, 10, 24).timestamp())
    end_time = int(datetime(2024, 10, 25).timestamp())
    
    # Create client with dates - just like DomeClient!
    dome = DomeBacktestClient({
        "api_key": api_key,
        "start_time": start_time,
        "end_time": end_time,
        "step": 3600,  # 1 hour intervals
        "initial_cash": 10000,  # Starting capital
    })
    
    print(f"Period: Oct 24-25, 2024")
    print(f"Strategy: Buy < $0.55, Sell > $0.65")
    print("-" * 50)
    
    # Run it - that's it! No get_prices function needed.
    result = await dome.run(my_strategy)
    
    print("-" * 50)
    print(f"Initial:  ${result.initial_cash}")
    print(f"Final:    ${result.final_value:.2f}")
    print(f"Return:   {result.total_return_pct:+.2f}%")
    print(f"Trades:   {len(result.trades)}")
    print("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())

