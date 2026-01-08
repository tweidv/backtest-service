"""Base API class with shared functionality for platform APIs."""

import asyncio
import inspect
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ..simulation.clock import SimulationClock
    from ..simulation.portfolio import Portfolio


class BasePlatformAPI:
    """Base class for platform APIs with shared functionality."""
    
    def __init__(
        self,
        platform: str,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limit: float = 1.1
    ):
        self.platform = platform
        self._client = real_client
        self._clock = clock
        self._portfolio = portfolio
        self._rate_limit = rate_limit  # seconds between API calls

    async def _call_api(self, method, params: dict, max_retries: int = 3):
        """
        Call API method with rate limiting, handling both sync and async methods.
        
        Handles rate limit errors (429) with exponential backoff retry.
        """
        import time
        
        for attempt in range(max_retries):
            # Rate limiting delay
            await asyncio.sleep(self._rate_limit)
            
            try:
                result = method(params)
                # If the SDK returns a coroutine, await it
                if inspect.iscoroutine(result):
                    result = await result
                return result
            except ValueError as e:
                # Check if it's a rate limit error
                error_str = str(e)
                if "429" in error_str or "Rate Limit" in error_str or "rate limit" in error_str.lower():
                    if attempt < max_retries - 1:
                        # Extract retry_after from error if available
                        retry_after = 10  # Default 10 seconds
                        if "retry_after" in error_str:
                            try:
                                import json
                                import re
                                # Try to extract retry_after from JSON in error message
                                json_match = re.search(r'\{[^}]+\}', error_str)
                                if json_match:
                                    error_data = json.loads(json_match.group())
                                    retry_after = error_data.get("retry_after", 10)
                            except:
                                pass
                        
                        wait_time = retry_after + (attempt * 2)  # Exponential backoff
                        print(f"[INFO] Rate limit hit, waiting {wait_time} seconds before retry {attempt + 1}/{max_retries}")
                        await asyncio.sleep(wait_time)
                        continue
                    else:
                        raise ValueError(f"Rate limit exceeded after {max_retries} retries. {error_str}")
                else:
                    # Not a rate limit error, re-raise
                    raise

    def _market_existed_at_time(self, market, at_time: int) -> bool:
        """Check if market existed (was created) at the given time."""
        return market.start_time <= at_time

    def _market_was_open_at_time(self, market, at_time: int) -> bool:
        """Check if market was open (tradeable) at the given time."""
        if market.start_time > at_time:
            return False  # Hadn't started yet
        if market.close_time and market.close_time <= at_time:
            return False  # Already closed
        return True

    def _market_was_closed_at_time(self, market, at_time: int) -> bool:
        """Check if market was already closed at the given time."""
        if market.start_time > at_time:
            return False  # Didn't exist yet
        if market.close_time and market.close_time <= at_time:
            return True  # Was closed
        return False

    def _cap_time_at_backtest(self, params: dict, time_key: str, is_milliseconds: bool = False):
        """
        Cap a time parameter at the current backtest time.
        
        Args:
            params: Parameter dict to modify
            time_key: Key in params to cap (e.g., 'end_time')
            is_milliseconds: If True, convert clock time to milliseconds
        """
        if time_key in params:
            multiplier = 1000 if is_milliseconds else 1
            params[time_key] = min(params[time_key], self._clock.current_time * multiplier)

