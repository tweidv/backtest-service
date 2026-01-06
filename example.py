"""
Example backtest usage.

Run with:
    set DOME_API_KEY=your-api-key
    python example.py
"""
import asyncio
import os
from decimal import Decimal

from backtest_service import DomeBacktestClient, BacktestRunner, Portfolio


# Example Polymarket token - "Will Bitcoin hit $100k in 2024?" YES token
# You can find token IDs via Dome API or Polymarket's Gamma API
TOKEN_ID = "21742633143463906290569050155826241533067272736897614950488156847949938836455"


async def my_strategy(dome: DomeBacktestClient, portfolio: Portfolio):
    """Simple strategy: buy on first tick, sell when price > 0.65"""
    try:
        price_data = await dome.polymarket.get_market_price({"token_id": TOKEN_ID})
        price = Decimal(str(price_data.price))
        print(f"  Price: {price}")
        
        # Buy if we have no position and have cash
        if TOKEN_ID not in portfolio.positions and portfolio.cash > 100:
            dome.polymarket.buy(TOKEN_ID, quantity=Decimal(10), price=price)
            print(f"  -> BUY 10 @ {price}")
        
        # Sell if price > 0.65 and we have position
        elif price > Decimal("0.65") and portfolio.positions.get(TOKEN_ID, 0) > 0:
            dome.polymarket.sell(TOKEN_ID, quantity=portfolio.positions[TOKEN_ID], price=price)
            print(f"  -> SELL @ {price}")
    
    except Exception as e:
        print(f"  Error: {e}")


async def get_prices(dome: DomeBacktestClient):
    """Get current prices for portfolio valuation"""
    try:
        price_data = await dome.polymarket.get_market_price({"token_id": TOKEN_ID})
        return {TOKEN_ID: Decimal(str(price_data.price))}
    except:
        return {}


async def main():
    api_key = os.environ.get("DOME_API_KEY")
    if not api_key:
        print("Set DOME_API_KEY environment variable")
        return
    
    # Short test: just 3 time steps (3 hours)
    runner = BacktestRunner(
        api_key=api_key,
        start_time=1730000000,  # Oct 27, 2024 (recent date with data)
        end_time=1730010800,    # ~3 hours later
        step=3600,              # 1 hour
        initial_cash=Decimal(10000),
    )
    
    print("Starting backtest...")
    result = await runner.run(my_strategy, get_prices)
    
    print(f"\n=== Results ===")
    print(f"Initial: ${result.initial_cash}")
    print(f"Final:   ${result.final_value}")
    print(f"Return:  {result.total_return_pct:.2f}%")
    print(f"Trades:  {len(result.trades)}")


if __name__ == "__main__":
    asyncio.run(main())

