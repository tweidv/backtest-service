"""
Example: Market Discovery during Backtest

Demonstrates how to discover markets dynamically without lookahead bias.
The strategy finds related markets and compares their prices.

Run with:
    set DOME_API_KEY=your-api-key
    python example_discovery.py
"""
import asyncio
import os
from datetime import datetime
from decimal import Decimal

from backtest_service import BacktestRunner


async def discovery_strategy(dome, portfolio):
    """Discover and analyze markets dynamically."""
    current_time = dome._clock.current_time
    
    # Only discover every 6 hours
    if (current_time - 1729800000) % (6 * 3600) != 0:
        return
    
    print(f"\n[{datetime.fromtimestamp(current_time).strftime('%Y-%m-%d %H:%M')}]")
    
    try:
        # Discover open, liquid markets
        response = await dome.polymarket.get_markets({
            "status": "open",
            "min_volume": 1000000,
            "limit": 5,
        })
        
        print(f"Found {len(response.markets)} markets:\n")
        
        for market in response.markets:
            # Get current price
            try:
                price_data = await dome.polymarket.get_market_price({
                    "token_id": market.side_a.id
                })
                price = price_data.price
            except:
                price = "N/A"
            
            print(f"  {market.title[:50]}...")
            print(f"    Status: {market.historical_status}")
            print(f"    Resolved: {market.was_resolved}")
            print(f"    Winner: {market.winning_side.label if market.winning_side else 'Hidden'}")
            print(f"    Price: {price}")
            print()
    
    except Exception as e:
        print(f"Error: {e}")


async def get_prices(dome):
    return {}


async def main():
    api_key = os.environ.get("DOME_API_KEY")
    if not api_key:
        print("Set DOME_API_KEY environment variable")
        return
    
    print("=" * 60)
    print("MARKET DISCOVERY EXAMPLE")
    print("=" * 60)
    print("Discovering markets at Oct 24, 2024 (before election)")
    print("Notice: Outcomes are HIDDEN - no lookahead bias!")
    print("=" * 60)
    
    runner = BacktestRunner(
        api_key=api_key,
        start_time=1729800000,  # Oct 24, 2024
        end_time=1729886400,    # Oct 25, 2024
        step=3600 * 6,          # 6 hour intervals
        initial_cash=Decimal("10000"),
    )
    
    await runner.run(discovery_strategy, get_prices)
    
    print("=" * 60)
    print("Notice: All markets showed 'Resolved: False'")
    print("The election outcome was hidden during the backtest!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

