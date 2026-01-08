"""Orderbook simulator for limit order matching."""

from decimal import Decimal
from typing import Optional, Dict, Any, List
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..api.base_api import BasePlatformAPI


class OrderbookSimulator:
    """Simulates orderbook matching for limit orders."""
    
    def __init__(self, base_api: "BasePlatformAPI"):
        self._base_api = base_api
        self._orderbook_cache: Dict[str, Dict] = {}
        # Store real client reference for API calls
        self._real_client = None
    
    async def get_historical_orderbook(self, token_id: str, timestamp: int, use_cache: bool = True) -> Optional[Dict]:
        """
        Fetch orderbook at specific timestamp.
        
        Args:
            token_id: Token ID (Polymarket) or ticker (Kalshi)
            timestamp: Unix timestamp in seconds
            use_cache: Whether to use cached orderbooks
        
        Returns:
            Orderbook snapshot dict with bids/asks, or None if not available
        """
        cache_key = f"{token_id}:{timestamp}"
        
        if use_cache and cache_key in self._orderbook_cache:
            return self._orderbook_cache[cache_key]
        
        try:
            if self._base_api.platform == "polymarket":
                # Polymarket orderbooks use milliseconds
                # Use the real API directly through base_api's call method
                orderbooks = await self._base_api._call_api(
                    self._base_api._real_api.markets.get_orderbooks,
                    {
                        "token_id": token_id,
                        "end_time": timestamp * 1000,  # Convert to milliseconds
                        "limit": 1  # Get snapshot at that time
                    }
                )
                
                if hasattr(orderbooks, 'snapshots') and orderbooks.snapshots:
                    # Filter to get snapshot at or before timestamp
                    for snapshot in orderbooks.snapshots:
                        snapshot_ts_ms = None
                        if hasattr(snapshot, 'timestamp'):
                            snapshot_ts_ms = snapshot.timestamp
                        elif isinstance(snapshot, dict):
                            snapshot_ts_ms = snapshot.get('timestamp')
                        
                        if snapshot_ts_ms and snapshot_ts_ms <= timestamp * 1000:
                            ob = self._parse_polymarket_orderbook(snapshot)
                            if use_cache:
                                self._orderbook_cache[cache_key] = ob
                            return ob
                
            elif self._base_api.platform == "kalshi":
                # Kalshi orderbooks use milliseconds
                # Extract ticker from token_id if needed
                ticker = token_id
                orderbooks = await self._base_api._call_api(
                    self._base_api._real_api.orderbooks.get_orderbooks,
                    {
                        "ticker": ticker,
                        "end_time": timestamp * 1000,  # Convert to milliseconds
                        "limit": 1
                    }
                )
                
                if hasattr(orderbooks, 'snapshots') and orderbooks.snapshots:
                    for snapshot in orderbooks.snapshots:
                        snapshot_ts_ms = None
                        if hasattr(snapshot, 'timestamp'):
                            snapshot_ts_ms = snapshot.timestamp
                        elif isinstance(snapshot, dict):
                            snapshot_ts_ms = snapshot.get('timestamp')
                        
                        if snapshot_ts_ms and snapshot_ts_ms <= timestamp * 1000:
                            ob = self._parse_kalshi_orderbook(snapshot)
                            if use_cache:
                                self._orderbook_cache[cache_key] = ob
                            return ob
        
        except Exception:
            # If orderbook fetch fails, return None (will use market price)
            pass
        
        return None
    
    def _parse_polymarket_orderbook(self, snapshot) -> Dict:
        """Parse Polymarket orderbook snapshot."""
        # Polymarket orderbook structure
        # bids: [[price, size], ...] (sorted best to worst)
        # asks: [[price, size], ...] (sorted best to worst)
        if hasattr(snapshot, 'bids') and hasattr(snapshot, 'asks'):
            bids = [[Decimal(str(b[0])), Decimal(str(b[1]))] for b in snapshot.bids] if snapshot.bids else []
            asks = [[Decimal(str(a[0])), Decimal(str(a[1]))] for a in snapshot.asks] if snapshot.asks else []
        elif isinstance(snapshot, dict):
            bids = [[Decimal(str(b[0])), Decimal(str(b[1]))] for b in snapshot.get('bids', [])]
            asks = [[Decimal(str(a[0])), Decimal(str(a[1]))] for a in snapshot.get('asks', [])]
        else:
            bids = []
            asks = []
        
        return {"bids": bids, "asks": asks}
    
    def _parse_kalshi_orderbook(self, snapshot) -> Dict:
        """Parse Kalshi orderbook snapshot."""
        # Kalshi orderbook structure
        # yes_bids: [[price_cents, count], ...]
        # no_bids: [[price_cents, count], ...]
        # For a YES buy, we need NO bids (selling NO = buying YES)
        # For a NO buy, we need YES bids (selling YES = buying NO)
        
        if hasattr(snapshot, 'orderbook'):
            ob_data = snapshot.orderbook
        elif isinstance(snapshot, dict):
            ob_data = snapshot.get('orderbook', {})
        else:
            ob_data = {}
        
        # Kalshi uses yes/no structure
        # For YES side: bids come from NO side (converted to YES price)
        # For NO side: bids come from YES side (converted to NO price)
        yes_bids = [[Decimal(str(b[0])) / Decimal(100), Decimal(str(b[1]))] 
                     for b in ob_data.get('yes', [])] if ob_data.get('yes') else []
        no_bids = [[Decimal(str(b[0])) / Decimal(100), Decimal(str(b[1]))] 
                    for b in ob_data.get('no', [])] if ob_data.get('no') else []
        
        # Kalshi binary market structure:
        # - To buy YES: we buy from NO sellers, so use NO bids and convert to YES price (1 - NO price)
        # - To buy NO: we buy from YES sellers, so use YES bids and convert to NO price (1 - YES price)
        # The actual price conversion is handled in can_fill_at_price() and get_market_price()
        # Here we just parse and store both sides for later use
        return {
            "yes_bids": yes_bids,
            "no_bids": no_bids,
            "bids": yes_bids + no_bids,  # Combined for compatibility with generic code
            "asks": []  # In binary markets, asks = opposite side bids (handled via conversion)
        }
    
    def can_fill_at_price(
        self, 
        orderbook: Optional[Dict], 
        side: str, 
        limit_price: Decimal, 
        size: Decimal,
        platform: str = "polymarket"
    ) -> bool:
        """
        Check if a limit order can fill at its price.
        
        Args:
            orderbook: Orderbook snapshot dict
            side: "YES", "NO", "BUY", "SELL", "yes", "no"
            limit_price: Limit price (0-1 for Polymarket, 0-1 for Kalshi after conversion)
            size: Order size
            platform: "polymarket" or "kalshi"
        
        Returns:
            True if order can fill, False otherwise
        """
        if not orderbook:
            return False  # No orderbook available
        
        side_upper = side.upper()
        
        if platform == "polymarket":
            if side_upper in ["YES", "BUY"]:
                # Buying YES: need asks (sellers) at or below limit_price
                asks = orderbook.get("asks", [])
                available = sum(qty for price, qty in asks if price <= limit_price)
                return available >= size
            else:  # NO or SELL
                # Selling NO or buying NO: need bids (buyers) at or above limit_price
                bids = orderbook.get("bids", [])
                available = sum(qty for price, qty in bids if price >= limit_price)
                return available >= size
        
        elif platform == "kalshi":
            if side_upper in ["YES", "yes"]:
                # Buying YES: need NO sellers (NO bids converted to YES price)
                # YES price = 1 - NO price
                no_bids = orderbook.get("no_bids", [])
                yes_price_limit = limit_price
                # NO sellers willing to sell at price that gives us YES at or below limit
                available = sum(
                    qty for no_price, qty in no_bids 
                    if (Decimal(1) - no_price) <= yes_price_limit
                )
                return available >= size
            else:  # NO or no
                # Buying NO: need YES sellers (YES bids converted to NO price)
                # NO price = 1 - YES price
                yes_bids = orderbook.get("yes_bids", [])
                no_price_limit = limit_price
                # YES sellers willing to sell at price that gives us NO at or below limit
                available = sum(
                    qty for yes_price, qty in yes_bids
                    if (Decimal(1) - yes_price) <= no_price_limit
                )
                return available >= size
        
        return False
    
    def get_market_price(
        self, 
        orderbook: Optional[Dict], 
        side: str, 
        platform: str = "polymarket"
    ) -> Optional[Decimal]:
        """
        Get best available price for market order.
        
        Args:
            orderbook: Orderbook snapshot dict
            side: "YES", "NO", "BUY", "SELL", "yes", "no"
            platform: "polymarket" or "kalshi"
        
        Returns:
            Best available price, or None if no liquidity
        """
        if not orderbook:
            return None
        
        side_upper = side.upper()
        
        if platform == "polymarket":
            if side_upper in ["YES", "BUY"]:
                # Best ask (lowest sell price)
                asks = orderbook.get("asks", [])
                return Decimal(asks[0][0]) if asks else None
            else:  # NO or SELL
                # Best bid (highest buy price)
                bids = orderbook.get("bids", [])
                return Decimal(bids[0][0]) if bids else None
        
        elif platform == "kalshi":
            if side_upper in ["YES", "yes"]:
                # For YES buy: use NO bids, convert to YES price
                no_bids = orderbook.get("no_bids", [])
                if no_bids:
                    no_price = Decimal(no_bids[0][0])
                    yes_price = Decimal(1) - no_price
                    return yes_price
                return None
            else:  # NO or no
                # For NO buy: use YES bids, convert to NO price
                yes_bids = orderbook.get("yes_bids", [])
                if yes_bids:
                    yes_price = Decimal(yes_bids[0][0])
                    no_price = Decimal(1) - yes_price
                    return no_price
                return None
        
        return None

