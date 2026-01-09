"""Rate limiter for Dome API with tier-based limits.

Supports Free, Dev, and Enterprise tiers with configurable limits.
Uses sliding window approach to track both per-second and per-10-second limits.
"""

import asyncio
import time
from collections import deque
from typing import Optional, Literal


class RateLimiter:
    """Rate limiter that enforces both QPS and per-10-second limits."""
    
    # Tier definitions
    TIER_LIMITS = {
        "free": {
            "qps": 1,
            "per_10s": 10
        },
        "dev": {
            "qps": 100,
            "per_10s": 500
        },
        "enterprise": {
            "qps": None,  # Custom - must be specified
            "per_10s": None  # Custom - must be specified
        }
    }
    
    def __init__(
        self,
        tier: Literal["free", "dev", "enterprise"] = "free",
        qps: Optional[int] = None,
        per_10s: Optional[int] = None
    ):
        """
        Initialize rate limiter.
        
        Args:
            tier: API tier ("free", "dev", or "enterprise")
            qps: Custom QPS limit (required for enterprise, optional override for others)
            per_10s: Custom per-10-second limit (required for enterprise, optional override for others)
        """
        self.tier = tier.lower()
        
        if self.tier not in self.TIER_LIMITS:
            raise ValueError(f"Invalid tier: {tier}. Must be one of: {list(self.TIER_LIMITS.keys())}")
        
        # Get tier defaults
        tier_config = self.TIER_LIMITS[self.tier]
        
        # Use provided values or tier defaults
        self.qps_limit = qps if qps is not None else tier_config["qps"]
        self.per_10s_limit = per_10s if per_10s is not None else tier_config["per_10s"]
        
        # Enterprise tier requires custom limits
        if self.tier == "enterprise" and (self.qps_limit is None or self.per_10s_limit is None):
            raise ValueError(
                "Enterprise tier requires custom limits. Provide qps and per_10s parameters."
            )
        
        # Sliding windows: deque of timestamps
        self._recent_requests = deque()  # All requests in last 10 seconds
        self._lock = asyncio.Lock()
    
    async def acquire(self):
        """
        Wait until a request can be made without violating rate limits.
        
        This method will block until both QPS and per-10-second limits are satisfied.
        """
        async with self._lock:
            now = time.time()
            
            # Clean up old requests (older than 10 seconds)
            while self._recent_requests and self._recent_requests[0] < now - 10:
                self._recent_requests.popleft()
            
            # Check per-10-second limit
            if len(self._recent_requests) >= self.per_10s_limit:
                # Need to wait until oldest request is 10 seconds old
                oldest_time = self._recent_requests[0]
                wait_time = 10 - (now - oldest_time) + 0.01  # Small buffer
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    now = time.time()
                    # Clean up again after waiting
                    while self._recent_requests and self._recent_requests[0] < now - 10:
                        self._recent_requests.popleft()
            
            # Check QPS limit (requests in last 1 second)
            recent_1s = [t for t in self._recent_requests if t >= now - 1]
            if len(recent_1s) >= self.qps_limit:
                # Need to wait until oldest request in last second is 1 second old
                oldest_1s = recent_1s[0]
                wait_time = 1 - (now - oldest_1s) + 0.01  # Small buffer
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
                    now = time.time()
                    # Clean up old requests after waiting
                    while self._recent_requests and self._recent_requests[0] < now - 10:
                        self._recent_requests.popleft()
            
            # Record this request
            self._recent_requests.append(now)
    
    def get_stats(self) -> dict:
        """Get current rate limiter statistics."""
        now = time.time()
        
        # Clean up old requests
        while self._recent_requests and self._recent_requests[0] < now - 10:
            self._recent_requests.popleft()
        
        recent_1s = [t for t in self._recent_requests if t >= now - 1]
        
        return {
            "tier": self.tier,
            "qps_limit": self.qps_limit,
            "per_10s_limit": self.per_10s_limit,
            "current_qps": len(recent_1s),
            "current_per_10s": len(self._recent_requests),
            "qps_remaining": max(0, self.qps_limit - len(recent_1s)),
            "per_10s_remaining": max(0, self.per_10s_limit - len(self._recent_requests))
        }

