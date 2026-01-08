"""
SUPER SIMPLE TEST STRATEGY - This will definitely make trades!
Just buys the first available market and holds it.
"""
import asyncio
import os
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv
from backtest_service import DomeBacktestClient

# Load environment variables
load_dotenv()

async def simple_test_strategy(dome):
    """
    Stupidly simple strategy: Buy the first market we find, no matter what.
    This will definitely make trades so we can verify the system works.
    """
    try:
        # Get ANY open markets (no filters)
        response = await dome.polymarket.get_markets({
            'status': 'open',
            'limit': 1  # Just get the first one
        })
        
        if not response.markets:
            print(f"[{datetime.fromtimestamp(dome._clock.current_time)}] No markets found")
            return
        
        # Get the first market
        market = response.markets[0]
        token_id = market.side_a.id
        
        # Get current price
        price_data = await dome.polymarket.get_market_price({'token_id': token_id})
        price = Decimal(str(price_data.price))
        
        # Check if we have a position
        position = dome.portfolio.positions.get(token_id, Decimal(0))
        cash = dome.portfolio.cash
        
        # SUPER SIMPLE: If we have cash and no position, BUY!
        if cash > 100 and position == 0:
            # Buy with 20% of our cash
            trade_size = (cash * Decimal('0.2')) / price
            trade_size = trade_size.quantize(Decimal('1'))
            if trade_size > 0:
                dome.polymarket.buy(token_id, trade_size, price)
                print(f"[{datetime.fromtimestamp(dome._clock.current_time)}] BUY {trade_size} @ {price:.4f} (Cost: ${trade_size * price:.2f})")
        
        # If we have a position, just hold it (don't sell)
        elif position > 0:
            print(f"[{datetime.fromtimestamp(dome._clock.current_time)}] HOLD {position} @ {price:.4f} (Value: ${position * price:.2f})")
    
    except Exception as e:
        print(f"[{datetime.fromtimestamp(dome._clock.current_time)}] Error: {e}")

async def main():
    api_key = os.environ.get("DOME_API_KEY")
    if not api_key:
        print("ERROR: DOME_API_KEY not set")
        return
    
    # Use a recent date range with more activity
    start_dt = datetime(2024, 10, 24)
    end_dt = datetime(2024, 10, 25)
    start_time = int(start_dt.timestamp())
    end_time = int(end_dt.timestamp())
    
    print(f"Running SIMPLE TEST backtest from {start_dt} to {end_dt}")
    print(f"Initial cash: $10,000")
    print("Strategy: Buy first market found, hold it\n")
    
    dome = DomeBacktestClient({
        "api_key": api_key,
        "start_time": start_time,
        "end_time": end_time,
        "step": 3600,  # 1 hour intervals
        "initial_cash": 10000.0,
    })
    
    result = await dome.run(simple_test_strategy)
    
    print("\n" + "="*50)
    print("BACKTEST RESULTS")
    print("="*50)
    print(f"Initial Cash: ${result.initial_cash}")
    print(f"Final Value: ${result.final_value}")
    print(f"Total Return: ${result.total_return}")
    print(f"Total Return %: {result.total_return_pct:.2f}%")
    print(f"Number of Trades: {len(result.trades)}")
    print("\nTrades:")
    if result.trades:
        for trade in result.trades:
            print(f"  {datetime.fromtimestamp(trade.timestamp)} - {trade.side.upper()} {trade.quantity} @ ${trade.price} (Value: ${trade.value})")
    else:
        print("  No trades executed")

if __name__ == "__main__":
    asyncio.run(main())

