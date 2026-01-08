"""Matching markets namespace: dome.matching_markets.*"""

from typing import TYPE_CHECKING

from ..base_api import BasePlatformAPI

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ...simulation.clock import SimulationClock
    from ...simulation.portfolio import Portfolio


class MatchingMarketsNamespace:
    """dome.matching_markets.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limit: float = 1.1
    ):
        self._real_client = real_client
        self._clock = clock
        self._portfolio = portfolio
        self._rate_limit = rate_limit

    async def get_matching_markets(self, params: dict) -> dict:
        """
        Find equivalent markets across platforms by Polymarket slug or Kalshi ticker.
        
        Matches: dome.matching_markets.get_matching_markets()
        
        Parameters (from Dome docs):
        - polymarket_market_slug: Optional - Array of Polymarket market slugs
        - kalshi_event_ticker: Optional - Array of Kalshi event tickers
        
        Note: Cannot provide both polymarket_market_slug and kalshi_event_ticker.
        At least one must be provided.
        
        Returns: Markets object with matching markets across platforms (Polymarket, Kalshi)
        """
        if 'polymarket_market_slug' not in params and 'kalshi_event_ticker' not in params:
            raise ValueError(
                "At least one of 'polymarket_market_slug' or 'kalshi_event_ticker' is required"
            )
        
        if 'polymarket_market_slug' in params and 'kalshi_event_ticker' in params:
            raise ValueError(
                "Cannot provide both 'polymarket_market_slug' and 'kalshi_event_ticker' - provide only one"
            )
        
        # Matching markets don't have time-based filtering, but we should filter
        # results to only show markets that existed at backtest time
        response = await self._call_api(self._real_client.matching_markets.get_matching_markets, params)
        
        # Filter markets to only include those that existed at backtest time
        if hasattr(response, 'markets') and response.markets:
            at_time = self._clock.current_time
            filtered_markets = {}
            
            for key, market_list in response.markets.items():
                filtered_list = []
                for market in market_list:
                    # Check if market existed at backtest time
                    # Polymarket markets: check if we can find the market
                    # Kalshi markets: check if we can find the market
                    # For now, include all - filtering would require additional API calls
                    # TODO: Add historical filtering if needed
                    filtered_list.append(market)
                
                if filtered_list:
                    filtered_markets[key] = filtered_list
            
            # Create filtered response
            try:
                import copy
                if hasattr(response, '__dict__'):
                    filtered_response = copy.copy(response)
                    filtered_response.markets = filtered_markets
                    return filtered_response
            except:
                class FilteredResponse:
                    def __init__(self, markets):
                        self.markets = markets
                return FilteredResponse(filtered_markets)
        
        return response

    async def get_matching_markets_by_sport(self, params: dict) -> dict:
        """
        Find equivalent markets by sport and date.
        
        Matches: dome.matching_markets.get_matching_markets_by_sport()
        
        Parameters (from Dome docs):
        - sport: Required - Sport abbreviation (nfl, mlb, cfb, nba, nhl, cbb)
        - date: Required - Date in YYYY-MM-DD format
        
        Returns: Markets object with matching markets for the specified sport and date
        """
        if 'sport' not in params:
            raise ValueError("sport is required for get_matching_markets_by_sport")
        
        if 'date' not in params:
            raise ValueError("date is required for get_matching_markets_by_sport (format: YYYY-MM-DD)")
        
        sport = params.get('sport')
        valid_sports = ['nfl', 'mlb', 'cfb', 'nba', 'nhl', 'cbb']
        if sport not in valid_sports:
            raise ValueError(f"sport must be one of: {', '.join(valid_sports)}. Got: {sport}")
        
        # Validate date format
        import re
        date = params.get('date')
        if not re.match(r'^\d{4}-\d{2}-\d{2}$', date):
            raise ValueError(f"date must be in YYYY-MM-DD format. Got: {date}")
        
        # Filter markets to only include those that existed at backtest time
        response = await self._call_api(
            self._real_client.matching_markets.get_matching_markets_by_sport,
            params
        )
        
        # Similar filtering as get_matching_markets
        if hasattr(response, 'markets') and response.markets:
            at_time = self._clock.current_time
            filtered_markets = {}
            
            for key, market_list in response.markets.items():
                filtered_list = []
                for market in market_list:
                    # TODO: Add historical filtering if needed
                    filtered_list.append(market)
                
                if filtered_list:
                    filtered_markets[key] = filtered_list
            
            try:
                import copy
                if hasattr(response, '__dict__'):
                    filtered_response = copy.copy(response)
                    filtered_response.markets = filtered_markets
                    return filtered_response
            except:
                class FilteredResponse:
                    def __init__(self, markets):
                        self.markets = markets
                return FilteredResponse(filtered_markets)
        
        return response

    async def _call_api(self, method, params: dict, max_retries: int = 3):
        """Call API method with rate limiting (shared with BasePlatformAPI logic)."""
        import asyncio
        import inspect
        
        for attempt in range(max_retries):
            await asyncio.sleep(self._rate_limit)
            
            try:
                result = method(params)
                if inspect.iscoroutine(result):
                    result = await result
                return result
            except ValueError as e:
                error_str = str(e)
                if "429" in error_str or "Rate Limit" in error_str or "rate limit" in error_str.lower():
                    if attempt < max_retries - 1:
                        retry_after = 10
                        wait_time = retry_after + (attempt * 2)
                        print(f"[INFO] Rate limit hit, waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise ValueError(f"Rate limit exceeded after {max_retries} retries. {error_str}")
                else:
                    raise

