"""Native SDK backtest clients for Polymarket and Kalshi.

These provide drop-in replacements for the native SDKs:
- PolymarketBacktestClient replaces py-clob-client ClobClient
- KalshiBacktestClient replaces kalshi KalshiClient
"""

from .polymarket import PolymarketBacktestClient
from .kalshi import KalshiBacktestClient

__all__ = ["PolymarketBacktestClient", "KalshiBacktestClient"]

