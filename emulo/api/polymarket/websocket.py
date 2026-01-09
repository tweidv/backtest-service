"""Polymarket WebSocket namespace: dome.polymarket.websocket.*"""

import asyncio
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Union, List, Optional, Callable, AsyncIterator
from decimal import Decimal

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ...simulation.clock import SimulationClock
    from ...simulation.portfolio import Portfolio
    from ..rate_limiter import RateLimiter


@dataclass
class WebSocketEvent:
    """
    Represents a WebSocket order event.
    
    Matches: dome_api_sdk.WebSocketOrderEvent
    """
    type: str  # "event" or "ack"
    subscription_id: Optional[str] = None
    data: Optional[dict] = None
    
    # For compatibility with SDK - data is the order data
    @property
    def user(self) -> Optional[str]:
        """Get user from event data (for SDK compatibility)."""
        return self.data.get("user") if self.data else None


@dataclass
class Subscription:
    """Represents a WebSocket subscription."""
    subscription_id: str
    filters: dict
    events: List[dict] = field(default_factory=list)  # Pre-fetched events sorted by timestamp
    current_index: int = 0  # Current position in events list
    on_event: Optional[Callable] = None
    request: Optional[dict] = None  # Original request for SDK compatibility


class PolymarketWebSocketNamespace:
    """dome.polymarket.websocket.* namespace - simulates WebSocket events for backtesting."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limiter: Union["RateLimiter", float, None] = None
    ):
        self._real_client = real_client
        self._clock = clock
        self._portfolio = portfolio
        self._rate_limiter = rate_limiter
        self._subscriptions: dict[str, Subscription] = {}
        self._subscription_counter = 0
    
    async def subscribe(
        self,
        users: Optional[List[str]] = None,
        condition_ids: Optional[List[str]] = None,
        market_slugs: Optional[List[str]] = None,
        on_event: Optional[Callable] = None
    ) -> str:
        """
        Subscribe to order events (simulated for backtesting).
        
        Matches: dome.polymarket.websocket.subscribe()
        
        Args:
            users: Optional list of wallet addresses to track
            condition_ids: Optional list of condition IDs to track
            market_slugs: Optional list of market slugs to track
            on_event: Optional callback function(event) called when events are emitted
        
        Returns:
            subscription_id (string)
        
        Limitations:
            - Wildcard subscriptions (users: ["*"]) are not supported
            - Multiple filter types require multiple API calls
        """
        # Build filters dict
        filters = {}
        if users:
            # Check for wildcard (not supported)
            if "*" in users:
                raise ValueError(
                    "Wildcard subscriptions (users: ['*']) are not supported in backtesting. "
                    "Please specify explicit wallet addresses."
                )
            filters["users"] = users
        if condition_ids:
            filters["condition_ids"] = condition_ids
        if market_slugs:
            filters["market_slugs"] = market_slugs
        
        if not filters:
            raise ValueError("At least one of users, condition_ids, or market_slugs must be provided")
        
        # Generate subscription ID (matches Dome format: sub_xxxxx)
        self._subscription_counter += 1
        subscription_id = f"sub_{self._subscription_counter:08d}"
        
        # Pre-fetch all matching orders for the backtest time range
        events = await self._fetch_matching_orders(filters)
        
        # Store request for get_active_subscriptions() compatibility
        request = {
            "action": "subscribe",
            "platform": "polymarket",
            "version": 1,
            "type": "orders",
            "filters": filters
        }
        
        subscription = Subscription(
            subscription_id=subscription_id,
            filters=filters,
            events=events,
            on_event=on_event
        )
        # Store request for SDK compatibility
        subscription.request = request
        
        self._subscriptions[subscription_id] = subscription
        
        # Return subscription_id (string) to match SDK
        return subscription_id
    
    async def _fetch_matching_orders(self, filters: dict) -> List[dict]:
        """
        Pre-fetch all orders matching the subscription filters.
        
        Handles multiple users/condition_ids/market_slugs by making multiple API calls.
        """
        all_orders = []
        
        # Get backtest time range from clock
        # Use a reasonable range - we'll filter during replay based on actual backtest times
        # Fetch from current time backwards and forwards to cover the backtest period
        current_time = self._clock.current_time
        start_time = current_time - (365 * 24 * 3600)  # 1 year ago (should cover most backtests)
        end_time = current_time + (365 * 24 * 3600)  # 1 year ahead
        
        # Fetch orders for each filter type
        if "users" in filters:
            users = filters["users"]
            if not isinstance(users, list):
                users = [users]
            
            for user in users:
                orders = await self._fetch_orders_paginated({
                    "user": user,
                    "start_time": start_time,
                    "end_time": end_time,
                    "limit": 1000
                })
                all_orders.extend(orders)
        
        if "condition_ids" in filters:
            condition_ids = filters["condition_ids"]
            if not isinstance(condition_ids, list):
                condition_ids = [condition_ids]
            
            for condition_id in condition_ids:
                orders = await self._fetch_orders_paginated({
                    "condition_id": condition_id,
                    "start_time": start_time,
                    "end_time": end_time,
                    "limit": 1000
                })
                all_orders.extend(orders)
        
        if "market_slugs" in filters:
            market_slugs = filters["market_slugs"]
            if not isinstance(market_slugs, list):
                market_slugs = [market_slugs]
            
            for market_slug in market_slugs:
                orders = await self._fetch_orders_paginated({
                    "market_slug": market_slug,
                    "start_time": start_time,
                    "end_time": end_time,
                    "limit": 1000
                })
                all_orders.extend(orders)
        
        # Remove duplicates (same order might match multiple filters)
        seen_order_hashes = set()
        unique_orders = []
        for order in all_orders:
            order_hash = order.get("order_hash") or order.get("tx_hash")
            if order_hash and order_hash not in seen_order_hashes:
                seen_order_hashes.add(order_hash)
                unique_orders.append(order)
        
        # Sort by timestamp
        unique_orders.sort(key=lambda x: x.get("timestamp", 0))
        
        return unique_orders
    
    async def _fetch_orders_paginated(self, params: dict) -> List[dict]:
        """Fetch all orders with pagination."""
        all_orders = []
        offset = 0
        limit = params.get("limit", 1000)
        
        while True:
            params_copy = params.copy()
            params_copy["offset"] = offset
            params_copy["limit"] = limit
            
            try:
                # Use the real API client to fetch orders
                # Note: We bypass the backtest client's time filtering here since we're pre-fetching
                response = await self._real_client.polymarket.orders.get_orders(params_copy)
                
                if hasattr(response, 'orders'):
                    orders = response.orders
                elif isinstance(response, dict) and 'orders' in response:
                    orders = response['orders']
                else:
                    orders = []
                
                if not orders:
                    break
                
                all_orders.extend(orders)
                
                # Check if there are more pages
                if hasattr(response, 'pagination'):
                    pagination = response.pagination
                elif isinstance(response, dict) and 'pagination' in response:
                    pagination = response['pagination']
                else:
                    pagination = {}
                
                has_more = pagination.get("has_more", False)
                if not has_more:
                    break
                
                offset += len(orders)
                
            except Exception as e:
                # If API call fails, break and return what we have
                break
        
        return all_orders
    
    async def unsubscribe(self, subscription_id: str):
        """
        Unsubscribe from order events.
        
        Matches: dome.polymarket.websocket.unsubscribe()
        
        Args:
            subscription_id: The subscription ID to unsubscribe from
        """
        if subscription_id in self._subscriptions:
            del self._subscriptions[subscription_id]
    
    async def update(
        self,
        subscription_id: str,
        users: Optional[List[str]] = None,
        condition_ids: Optional[List[str]] = None,
        market_slugs: Optional[List[str]] = None
    ):
        """
        Update an existing subscription with new filters.
        
        Matches: dome.polymarket.websocket.update()
        
        Args:
            subscription_id: The subscription ID to update
            users: Optional list of wallet addresses to track
            condition_ids: Optional list of condition IDs to track
            market_slugs: Optional list of market slugs to track
        """
        if subscription_id not in self._subscriptions:
            raise ValueError(f"Subscription {subscription_id} not found")
        
        # Build new filters
        filters = {}
        if users:
            if "*" in users:
                raise ValueError(
                    "Wildcard subscriptions (users: ['*']) are not supported in backtesting. "
                    "Please specify explicit wallet addresses."
                )
            filters["users"] = users
        if condition_ids:
            filters["condition_ids"] = condition_ids
        if market_slugs:
            filters["market_slugs"] = market_slugs
        
        if not filters:
            raise ValueError("At least one of users, condition_ids, or market_slugs must be provided")
        
        subscription = self._subscriptions[subscription_id]
        
        # Re-fetch orders with new filters
        events = await self._fetch_matching_orders(filters)
        
        # Update subscription
        subscription.filters = filters
        subscription.events = events
        subscription.current_index = 0  # Reset to beginning
        
        # Update request
        subscription.request = {
            "action": "subscribe",
            "platform": "polymarket",
            "version": 1,
            "type": "orders",
            "filters": filters
        }
    
    def get_active_subscriptions(self) -> List[Subscription]:
        """Get all active subscriptions."""
        return list(self._subscriptions.values())
    
    async def process_events(self):
        """
        Process and emit events for current backtest time.
        
        This should be called each tick during backtest execution.
        """
        current_time = self._clock.current_time
        
        for subscription in self._subscriptions.values():
            # Emit events that occurred at or before current time
            while subscription.current_index < len(subscription.events):
                event_data = subscription.events[subscription.current_index]
                event_timestamp = event_data.get("timestamp", 0)
                
                # Only emit events up to current time
                if event_timestamp > current_time:
                    break
                
                # Create WebSocket event format
                ws_event = WebSocketEvent(
                    type="event",
                    subscription_id=subscription.subscription_id,
                    data=event_data
                )
                
                # Call on_event callback if provided
                if subscription.on_event:
                    try:
                        if asyncio.iscoroutinefunction(subscription.on_event):
                            await subscription.on_event(ws_event)
                        else:
                            subscription.on_event(ws_event)
                    except Exception as e:
                        # Log error but continue processing
                        pass
                
                subscription.current_index += 1
    
    async def __aenter__(self):
        """Context manager entry (no-op for backtesting)."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - disconnect and clear subscriptions."""
        await self.disconnect()
    
    async def connect(self):
        """Connect to WebSocket (simulated, no-op for backtesting)."""
        pass
    
    async def disconnect(self):
        """Disconnect and clear all subscriptions."""
        self._subscriptions.clear()

