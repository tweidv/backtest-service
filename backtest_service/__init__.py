from .api import (
    DomeBacktestClient,
    HistoricalMarket,
    HistoricalMarketsResponse,
    HistoricalKalshiMarket,
    HistoricalKalshiMarketsResponse,
)
from .simulation import BacktestRunner, SimulationClock, Portfolio
from .models import BacktestResult, Trade

# Native SDK clients (optional - only import if needed)
try:
    from .native import PolymarketBacktestClient, KalshiBacktestClient
    __all__ = [
        "DomeBacktestClient",
        "HistoricalMarket",
        "HistoricalMarketsResponse",
        "HistoricalKalshiMarket",
        "HistoricalKalshiMarketsResponse",
        "BacktestRunner",
        "SimulationClock",
        "Portfolio",
        "BacktestResult",
        "Trade",
        "PolymarketBacktestClient",
        "KalshiBacktestClient",
    ]
except ImportError:
    __all__ = [
        "DomeBacktestClient",
        "HistoricalMarket",
        "HistoricalMarketsResponse",
        "HistoricalKalshiMarket",
        "HistoricalKalshiMarketsResponse",
        "BacktestRunner",
        "SimulationClock",
        "Portfolio",
        "BacktestResult",
        "Trade",
    ]

