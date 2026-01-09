"""Kalshi API namespace - matches Dome's structure: dome.kalshi.*"""

from .namespace import KalshiNamespace
from .markets import KalshiMarketsNamespace
from .orderbooks import KalshiOrderbooksNamespace
from .trades import KalshiTradesNamespace

__all__ = [
    'KalshiNamespace',
    'KalshiMarketsNamespace',
    'KalshiOrderbooksNamespace',
    'KalshiTradesNamespace',
]

