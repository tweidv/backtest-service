"""
ULTRA SIMPLE TEST STRATEGY - Uses hardcoded token ID to avoid rate limits
This will definitely make trades and verify the system works!
"""
import asyncio
import os
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv
from backtest_service import DomeBacktestClient

# Load environment variables
load_dotenv()

# Use a known token ID from the example (Bitcoin $100k market)
TOKEN_ID = "21742633143463906290569050155826241533067272736897614950488156847949938836455"

async def ultra_simple_strategy(dome):
    """
    Stupidly simple strategy: Buy if price < 0.55, sell if price > 0.65
    Uses hardcoded token ID to avoid market discovery API calls.
    """
    try:
        # Get price for the known token
        price_data = await dome.polymarket.get_market_price({'token_id': TOKEN_ID})
        price = Decimal(str(price_data.price))
        
        # Check position
        position = dome.portfolio.positions.get(TOKEN_ID, Decimal(0))
        cash = dome.portfolio.cash
        
        # SUPER SIMPLE LOGIC:
        # Buy if price is low and we have cash
        if price < Decimal('0.55') and cash > 500 and position == 0:
            # Buy with $500
            trade_size = (Decimal('500') / price).quantize(Decimal('1'))
            if trade_size > 0:
                dome.polymarket.buy(TOKEN_ID, trade_size, price)
                print(f"[{datetime.fromtimestamp(dome._clock.current_time)}] BUY {trade_size} @ {price:.4f} (Cost: ${trade_size * price:.2f})")
        
        # Sell if price is high and we have position
        elif price > Decimal('0.65') and position > 0:
            dome.polymarket.sell(TOKEN_ID, position, price)
            print(f"[{datetime.fromtimestamp(dome._clock.current_time)}] SELL {position} @ {price:.4f} (Value: ${position * price:.2f})")
        
        else:
            if position > 0:
                print(f"[{datetime.fromtimestamp(dome._clock.current_time)}] HOLD {position} @ {price:.4f} (Value: ${position * price:.2f})")
            else:
                print(f"[{datetime.fromtimestamp(dome._clock.current_time)}] WAIT @ {price:.4f} (Cash: ${cash:.2f})")
    
    except Exception as e:
        print(f"[{datetime.fromtimestamp(dome._clock.current_time)}] Error: {e}")

async def main():
    api_key = os.environ.get("DOME_API_KEY")
    if not api_key:
        print("ERROR: DOME_API_KEY not set")
        return
    
    # Use a recent date range - but with larger step to reduce API calls
    start_dt = datetime(2024, 10, 24)
    end_dt = datetime(2024, 10, 25)
    start_time = int(start_dt.timestamp())
    end_time = int(end_dt.timestamp())
    
    print(f"Running ULTRA SIMPLE TEST backtest from {start_dt} to {end_dt}")
    print(f"Initial cash: $10,000")
    print(f"Strategy: Buy < $0.55, Sell > $0.65 (using hardcoded token ID)")
    print(f"Step: 6 hours (to reduce API calls)\n")
    
    dome = DomeBacktestClient({
        "api_key": api_key,
        "start_time": start_time,
        "end_time": end_time,
        "step": 3600 * 6,  # 6 hour intervals to reduce API calls
        "initial_cash": 10000.0,
    })
    
    result = await dome.run(ultra_simple_strategy)
    
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
    print("="*50)

if __name__ == "__main__":
    asyncio.run(main())

