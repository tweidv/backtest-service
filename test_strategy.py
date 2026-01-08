"""
Test script to run a strategy outside the UI
"""
import asyncio
import os
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv
from backtest_service import DomeBacktestClient

# Load environment variables
load_dotenv()

# The strategy from the UI
async def my_strategy(dome):
    """
    Momentum-based trading strategy:
    - Discovers high-volume markets dynamically
    - Buys on price drops (mean reversion)
    - Sells on price increases (take profit)
    - Manages position sizes (10% of cash per trade)
    """
    try:
        # Discover liquid markets (high volume = better liquidity)
        response = await dome.polymarket.get_markets({
            'status': 'open',
            'min_volume': 500000,  # $500k+ volume
            'limit': 3
        })
        
        if not response.markets:
            return  # No markets found
        
        # Trade the first liquid market
        market = response.markets[0]
        token_id = market.side_a.id
        
        # Get current price
        price_data = await dome.polymarket.get_market_price({'token_id': token_id})
        price = Decimal(str(price_data.price))
        
        # Check if we have a position
        position = dome.portfolio.positions.get(token_id, Decimal(0))
        cash = dome.portfolio.cash
        
        # Strategy: Mean reversion with momentum
        # Buy when price is low (below 0.45) and we have cash
        if price < Decimal('0.45') and cash > 100 and position == 0:
            # Risk 10% of cash per trade
            trade_size = (cash * Decimal('0.1')) / price
            trade_size = trade_size.quantize(Decimal('1'))
            if trade_size > 0:
                dome.polymarket.buy(token_id, trade_size, price)
                print(f"[{datetime.fromtimestamp(dome._clock.current_time)}] BUY {trade_size} @ {price:.4f}")
        
        # Sell when price is high (above 0.65) and we have position
        elif price > Decimal('0.65') and position > 0:
            dome.polymarket.sell(token_id, position, price)
            print(f"[{datetime.fromtimestamp(dome._clock.current_time)}] SELL {position} @ {price:.4f}")
        
        # Take profit at 0.60 if we have position
        elif price > Decimal('0.60') and position > 0:
            # Sell 50% of position to lock in profit
            sell_qty = (position * Decimal('0.5')).quantize(Decimal('1'))
            if sell_qty > 0:
                dome.polymarket.sell(token_id, sell_qty, price)
                print(f"[{datetime.fromtimestamp(dome._clock.current_time)}] SELL {sell_qty} @ {price:.4f}")
    
    except Exception as e:
        # Silently handle API errors (rate limits, etc.)
        print(f"Error: {e}")

async def main():
    api_key = os.environ.get("DOME_API_KEY")
    if not api_key:
        print("ERROR: DOME_API_KEY not set")
        return
    
    # Use the same date range as the UI
    start_dt = datetime(2024, 10, 24)
    end_dt = datetime(2024, 10, 25)
    start_time = int(start_dt.timestamp())
    end_time = int(end_dt.timestamp())
    
    print(f"Running backtest from {start_dt} to {end_dt}")
    print(f"Initial cash: $10,000")
    
    dome = DomeBacktestClient({
        "api_key": api_key,
        "start_time": start_time,
        "end_time": end_time,
        "step": 3600,  # 1 hour intervals
        "initial_cash": 10000.0,
    })
    
    result = await dome.run(my_strategy)
    
    print("\n" + "="*50)
    print("BACKTEST RESULTS")
    print("="*50)
    print(f"Initial Cash: ${result.initial_cash}")
    print(f"Final Value: ${result.final_value}")
    print(f"Total Return: ${result.total_return}")
    print(f"Total Return %: {result.total_return_pct:.2f}%")
    print(f"Number of Trades: {len(result.trades)}")
    print("\nTrades:")
    for trade in result.trades:
        print(f"  {datetime.fromtimestamp(trade.timestamp)} - {trade.side.upper()} {trade.quantity} @ ${trade.price} (Value: ${trade.value})")

if __name__ == "__main__":
    asyncio.run(main())

