"""Backtest service API client and models."""

from .client import DomeBacktestClient
from .models import (
    HistoricalMarket,
    HistoricalMarketsResponse,
    HistoricalKalshiMarket,
    HistoricalKalshiMarketsResponse,
)
from .base_api import BasePlatformAPI
from .polymarket_namespaces import PolymarketNamespace
from .kalshi_namespaces import KalshiNamespace

__all__ = [
    'DomeBacktestClient',
    'HistoricalMarket',
    'HistoricalMarketsResponse',
    'HistoricalKalshiMarket',
    'HistoricalKalshiMarketsResponse',
    'BasePlatformAPI',
    'PolymarketNamespace',
    'KalshiNamespace',
]
