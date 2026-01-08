"""Polymarket wallet namespace: dome.polymarket.wallet.*"""

from typing import TYPE_CHECKING

from ..base_api import BasePlatformAPI

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ...simulation.clock import SimulationClock
    from ...simulation.portfolio import Portfolio


class PolymarketWalletNamespace(BasePlatformAPI):
    """dome.polymarket.wallet.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limit: float = 1.1
    ):
        super().__init__("polymarket", real_client, clock, portfolio, rate_limit)
        self._real_api = real_client.polymarket

    async def get_wallet(self, params: dict) -> dict:
        """
        Get wallet information up to backtest time.
        
        Matches: dome.polymarket.wallet.get_wallet()
        
        Parameters (from Dome docs):
        - eoa: Optional - EOA wallet address (either eoa or proxy required, not both)
        - proxy: Optional - Proxy wallet address (either eoa or proxy required, not both)
        - with_metrics: Optional - Include trading metrics (true/false string)
        - start_time: Optional - Unix timestamp (seconds) for metrics calculation start
        - end_time: Optional - Unix timestamp (seconds) for metrics calculation end
        
        Note: Either eoa or proxy must be provided (but not both).
        """
        if 'eoa' not in params and 'proxy' not in params:
            raise ValueError("Either 'eoa' or 'proxy' wallet address is required for get_wallet")
        
        if 'eoa' in params and 'proxy' in params:
            raise ValueError("Cannot provide both 'eoa' and 'proxy' - provide only one")
        
        params = params.copy()
        at_time = self._clock.current_time
        
        # Cap end_time at backtest time if provided (wallet uses seconds)
        if 'end_time' in params:
            params['end_time'] = min(params['end_time'], at_time)
        
        # Cap start_time if provided
        if 'start_time' in params:
            params['start_time'] = min(params['start_time'], at_time)
        
        return await self._call_api(self._real_api.wallet.get_wallet, params)

    async def get_wallet_pnl(self, params: dict) -> dict:
        """
        Get wallet PnL up to backtest time.
        
        Matches: dome.polymarket.wallet.get_wallet_pnl()
        
        Parameters (from Dome docs):
        - wallet_address: Required - Wallet address (path parameter, SDK handles it)
        - granularity: Required - day, week, month, year, or all
        - start_time: Optional - Unix timestamp (seconds). Defaults to first day of first trade
        - end_time: Optional - Unix timestamp (seconds). Defaults to current date
        
        Note: This tracks REALIZED PnL only (from sells/redeems), not unrealized.
        """
        if 'wallet_address' not in params:
            raise ValueError("wallet_address is required for get_wallet_pnl")
        
        if 'granularity' not in params:
            raise ValueError("granularity is required for get_wallet_pnl (must be: day, week, month, year, or all)")
        
        granularity = params.get('granularity')
        if granularity not in ['day', 'week', 'month', 'year', 'all']:
            raise ValueError(f"granularity must be one of: day, week, month, year, all. Got: {granularity}")
        
        params = params.copy()
        at_time = self._clock.current_time
        
        # Cap end_time at backtest time (wallet_pnl uses seconds)
        if 'end_time' in params:
            params['end_time'] = min(params['end_time'], at_time)
        else:
            params['end_time'] = at_time
        
        # Cap start_time if provided
        if 'start_time' in params:
            params['start_time'] = min(params['start_time'], at_time)
        
        return await self._call_api(self._real_api.wallet.get_wallet_pnl, params)

