"""
COMPREHENSIVE TEST STRATEGY - Tests all features:
- Market discovery (get_markets)
- Price fetching (get_market_price)
- Buying and selling
- Portfolio management
"""
import asyncio
import os
from datetime import datetime
from decimal import Decimal
from dotenv import load_dotenv
from backtest_service import DomeBacktestClient

# Load environment variables
load_dotenv()

async def comprehensive_test_strategy(dome):
    """
    Comprehensive test strategy that:
    1. Discovers markets dynamically
    2. Gets prices for multiple markets
    3. Makes buy/sell trades
    4. Tests portfolio management
    """
    try:
        # FEATURE 1: Market Discovery
        print(f"\n[{datetime.fromtimestamp(dome._clock.current_time)}] Discovering markets...")
        response = await dome.polymarket.get_markets({
            'status': 'open',
            'min_volume': 100000,  # Lower threshold to find more markets
            'limit': 5  # Get 5 markets
        })
        
        print(f"  Found {len(response.markets)} markets")
        
        if not response.markets:
            print("  No markets found, skipping this time step")
            return
        
        # FEATURE 2: Analyze multiple markets and pick one to trade
        best_market = None
        best_price = None
        
        for market in response.markets[:3]:  # Check first 3 markets
            try:
                # FEATURE 3: Get market price
                price_data = await dome.polymarket.get_market_price({
                    'token_id': market.side_a.id
                })
                price = Decimal(str(price_data.price))
                
                print(f"  Market: {market.title[:50]}...")
                print(f"    Price: ${price:.4f}")
                print(f"    Status: {market.historical_status}")
                print(f"    Resolved: {market.was_resolved}")
                
                # Pick the market with price closest to 0.50 (good entry point)
                if best_market is None or abs(price - Decimal('0.50')) < abs(best_price - Decimal('0.50')):
                    best_market = market
                    best_price = price
                    
            except Exception as e:
                print(f"  Error getting price for market: {e}")
                continue
        
        if not best_market:
            print("  No valid markets to trade")
            return
        
        token_id = best_market.side_a.id
        price = best_price
        
        # FEATURE 4: Check portfolio
        position = dome.portfolio.positions.get(token_id, Decimal(0))
        cash = dome.portfolio.cash
        
        print(f"\n  Portfolio Status:")
        print(f"    Cash: ${cash:.2f}")
        print(f"    Position in {token_id[:20]}...: {position}")
        
        # FEATURE 5: Trading Logic - Buy low, sell high
        # Buy if price is low (below 0.45) and we have cash
        if price < Decimal('0.45') and cash > 1000 and position == 0:
            # Use 20% of cash
            trade_amount = cash * Decimal('0.2')
            trade_size = (trade_amount / price).quantize(Decimal('1'))
            
            if trade_size > 0:
                print(f"\n  >>> BUYING {trade_size} tokens @ ${price:.4f}")
                dome.polymarket.buy(token_id, trade_size, price)
                print(f"    Cost: ${trade_size * price:.2f}")
                print(f"    New cash: ${dome.portfolio.cash:.2f}")
                print(f"    New position: {dome.portfolio.positions.get(token_id, 0)}")
        
        # Sell if price is high (above 0.70) and we have position
        elif price > Decimal('0.70') and position > 0:
            print(f"\n  <<< SELLING {position} tokens @ ${price:.4f}")
            dome.polymarket.sell(token_id, position, price)
            print(f"    Revenue: ${position * price:.2f}")
            print(f"    New cash: ${dome.portfolio.cash:.2f}")
            print(f"    New position: {dome.portfolio.positions.get(token_id, 0)}")
        
        # Take profit if price is decent (above 0.60) and we have position
        elif price > Decimal('0.60') and position > 0:
            # Sell 50% to lock in profit
            sell_qty = (position * Decimal('0.5')).quantize(Decimal('1'))
            if sell_qty > 0:
                print(f"\n  $$$ TAKING PROFIT: Selling {sell_qty} tokens @ ${price:.4f}")
                dome.polymarket.sell(token_id, sell_qty, price)
                print(f"    Revenue: ${sell_qty * price:.2f}")
                print(f"    New cash: ${dome.portfolio.cash:.2f}")
                print(f"    Remaining position: {dome.portfolio.positions.get(token_id, 0)}")
        
        else:
            if position > 0:
                position_value = position * price
                print(f"\n  --- HOLDING {position} tokens @ ${price:.4f} (Value: ${position_value:.2f})")
            else:
                print(f"\n  --- WAITING (Price: ${price:.4f}, Target: < $0.45 to buy, > $0.70 to sell)")
    
    except Exception as e:
        print(f"\n  !!! Error in strategy: {e}")
        import traceback
        traceback.print_exc()

async def main():
    api_key = os.environ.get("DOME_API_KEY")
    if not api_key:
        print("ERROR: DOME_API_KEY not set")
        return
    
    # Use a date range with larger step to reduce API calls but still test thoroughly
    start_dt = datetime(2024, 10, 24)
    end_dt = datetime(2024, 10, 25)
    start_time = int(start_dt.timestamp())
    end_time = int(end_dt.timestamp())
    
    print("="*70)
    print("COMPREHENSIVE FEATURE TEST")
    print("="*70)
    print(f"Period: {start_dt.date()} to {end_dt.date()}")
    print(f"Initial cash: $10,000")
    print(f"Step: 6 hours (to reduce API calls)")
    print("\nStrategy Features:")
    print("  [X] Market discovery (get_markets)")
    print("  [X] Price fetching (get_market_price)")
    print("  [X] Dynamic market selection")
    print("  [X] Buy/sell trading")
    print("  [X] Portfolio management")
    print("  [X] Take profit logic")
    print("="*70)
    
    dome = DomeBacktestClient({
        "api_key": api_key,
        "start_time": start_time,
        "end_time": end_time,
        "step": 3600 * 6,  # 6 hour intervals
        "initial_cash": 10000.0,
    })
    
    result = await dome.run(comprehensive_test_strategy)
    
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    print(f"Initial Cash:     ${result.initial_cash}")
    print(f"Final Value:      ${result.final_value}")
    print(f"Total Return:     ${result.total_return}")
    print(f"Total Return %:   {result.total_return_pct:+.2f}%")
    print(f"Number of Trades: {len(result.trades)}")
    
    if result.trades:
        print("\nTrade History:")
        for i, trade in enumerate(result.trades, 1):
            trade_time = datetime.fromtimestamp(trade.timestamp)
            print(f"  {i}. {trade_time.strftime('%Y-%m-%d %H:%M')} - {trade.side.upper():4s} "
                  f"{trade.quantity:>8.0f} @ ${trade.price:.4f} = ${trade.value:.2f}")
    else:
        print("\nNo trades executed")
    
    # Show final portfolio
    print(f"\nFinal Portfolio:")
    print(f"  Cash: ${dome.portfolio.cash:.2f}")
    if dome.portfolio.positions:
        print(f"  Positions:")
        for token_id, qty in dome.portfolio.positions.items():
            print(f"    {token_id[:30]}...: {qty}")
    else:
        print(f"  No open positions")
    
    print("="*70)

if __name__ == "__main__":
    asyncio.run(main())

