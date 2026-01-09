"""Backtest service API client and models."""

from .client import DomeBacktestClient
from .models import (
    HistoricalMarket,
    HistoricalMarketsResponse,
    HistoricalKalshiMarket,
    HistoricalKalshiMarketsResponse,
)
from .base_api import BasePlatformAPI
from .rate_limiter import RateLimiter
from .polymarket import PolymarketNamespace
from .kalshi import KalshiNamespace
from .matching_markets import MatchingMarketsNamespace
from .crypto_prices import CryptoPricesNamespace

__all__ = [
    'DomeBacktestClient',
    'HistoricalMarket',
    'HistoricalMarketsResponse',
    'HistoricalKalshiMarket',
    'HistoricalKalshiMarketsResponse',
    'BasePlatformAPI',
    'RateLimiter',
    'PolymarketNamespace',
    'KalshiNamespace',
    'MatchingMarketsNamespace',
    'CryptoPricesNamespace',
]
