"""Crypto prices namespace - matches Dome's structure: dome.crypto_prices.*"""

from .namespace import CryptoPricesNamespace
from .binance import BinanceNamespace
from .chainlink import ChainlinkNamespace

__all__ = [
    'CryptoPricesNamespace',
    'BinanceNamespace',
    'ChainlinkNamespace',
]

