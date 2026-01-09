"""Polymarket API namespace - matches Dome's structure: dome.polymarket.*"""

from .namespace import PolymarketNamespace
from .markets import PolymarketMarketsNamespace
from .orders import PolymarketOrdersNamespace
from .wallet import PolymarketWalletNamespace
from .activity import PolymarketActivityNamespace
from .websocket import PolymarketWebSocketNamespace

__all__ = [
    'PolymarketNamespace',
    'PolymarketMarketsNamespace',
    'PolymarketOrdersNamespace',
    'PolymarketWalletNamespace',
    'PolymarketActivityNamespace',
    'PolymarketWebSocketNamespace',
]

