"""Base API class with shared functionality for platform APIs.

This module provides the BasePlatformAPI class that all platform-specific
API namespaces inherit from. It includes:
- Rate-limited API calling with retry logic
- Historical time filtering helpers
- Market existence/status checking
"""

import asyncio
import inspect
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ..simulation.clock import SimulationClock
    from ..simulation.portfolio import Portfolio
    from .rate_limiter import RateLimiter


class BasePlatformAPI:
    """Base class for platform APIs with shared functionality."""
    
    def __init__(
        self,
        platform: str,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limiter: Union["RateLimiter", float, None] = None
    ):
        self.platform = platform
        self._client = real_client
        self._real_api = None  # Will be set by subclasses
        self._clock = clock
        self._portfolio = portfolio
        
        # Handle rate limiter: accept RateLimiter, float (backward compat), or None (default to free tier)
        if rate_limiter is None:
            from .rate_limiter import RateLimiter
            self._rate_limiter = RateLimiter(tier="free")
        elif isinstance(rate_limiter, float):
            # Backward compatibility: convert old float rate_limit to a simple limiter
            # For 1.1s delay, that's roughly 0.9 QPS, so use free tier
            from .rate_limiter import RateLimiter
            self._rate_limiter = RateLimiter(tier="free")
        else:
            self._rate_limiter = rate_limiter
        
        # UX/Logging (set by DomeBacktestClient)
        self._verbose = False
        self._log_level = "INFO"
        self._on_api_call = None
        self._dome_client = None
        
        # Initialize order simulation components (lazy initialization)
        self._orderbook_sim = None
        self._order_manager = None
    
    def _init_order_simulation(self):
        """Lazy initialization of order simulation components."""
        if self._orderbook_sim is None:
            from ..simulation.orderbook import OrderbookSimulator
            from ..simulation.orders import OrderManager
            
            self._orderbook_sim = OrderbookSimulator(self)
            self._order_manager = OrderManager(self._clock, self._portfolio, self._orderbook_sim)
            # Set real client reference
            self._orderbook_sim._real_client = self._client

    async def _call_api(self, method, params: dict, max_retries: int = 3):
        """
        Call API method with rate limiting, handling both sync and async methods.
        
        Handles rate limit errors (429) with exponential backoff retry.
        """
        import time
        from datetime import datetime
        
        # Extract endpoint name for logging
        endpoint_name = getattr(method, '__name__', 'unknown')
        if hasattr(method, '__self__'):
            # Try to get the full path
            class_name = method.__self__.__class__.__name__ if hasattr(method.__self__, '__class__') else 'unknown'
            endpoint_name = f"{class_name}.{endpoint_name}"
        
        # Log API call if verbose
        if self._verbose and self._log_level in ["DEBUG", "INFO"]:
            # Create a readable params summary
            params_summary = {}
            for key, value in params.items():
                if key == 'token_id' or key == 'condition_id':
                    params_summary[key] = f"{str(value)[:20]}..." if len(str(value)) > 20 else value
                elif isinstance(value, (int, float, str)):
                    params_summary[key] = value
                else:
                    params_summary[key] = type(value).__name__
            
            current_time_str = datetime.fromtimestamp(self._clock.current_time).strftime('%H:%M:%S')
            print(f"  [API] {current_time_str} {self.platform}.{endpoint_name}({params_summary})")
        
        for attempt in range(max_retries):
            # Rate limiting: wait until we can make a request
            await self._rate_limiter.acquire()
            
            try:
                result = method(params)
                # If the SDK returns a coroutine, await it
                if inspect.iscoroutine(result):
                    result = await result
                
                # Log response if verbose
                if self._verbose and self._log_level == "DEBUG":
                    result_summary = "OK"
                    if hasattr(result, 'markets'):
                        result_summary = f"{len(result.markets)} markets"
                    elif hasattr(result, 'price'):
                        result_summary = f"price={result.price}"
                    elif hasattr(result, 'snapshots'):
                        result_summary = f"{len(result.snapshots)} snapshots"
                    print(f"    -> {result_summary}")
                
                # Call on_api_call callback if provided
                if self._on_api_call:
                    await self._on_api_call(endpoint_name, params, result)
                
                return result
            except ValueError as e:
                # Check if it's a rate limit error
                error_str = str(e)
                if "429" in error_str or "Rate Limit" in error_str or "rate limit" in error_str.lower():
                    if attempt < max_retries - 1:
                        # Extract retry_after from error if available
                        retry_after = 1  # Default 1 second
                        if "retry_after" in error_str:
                            try:
                                import json
                                import re
                                # Try to extract retry_after from JSON in error message
                                json_match = re.search(r'\{[^}]+\}', error_str)
                                if json_match:
                                    error_data = json.loads(json_match.group())
                                    retry_after = error_data.get("retry_after", 1)
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

