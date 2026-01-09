"""Polymarket wallet namespace: dome.polymarket.wallet.*"""

from typing import TYPE_CHECKING, Union

from ..base_api import BasePlatformAPI

if TYPE_CHECKING:
    from dome_api_sdk import DomeClient
    from ...simulation.clock import SimulationClock
    from ...simulation.portfolio import Portfolio
    from ..rate_limiter import RateLimiter


class PolymarketWalletNamespace(BasePlatformAPI):
    """dome.polymarket.wallet.* namespace - matches Dome's structure exactly."""
    
    def __init__(
        self,
        real_client: "DomeClient",
        clock: "SimulationClock",
        portfolio: "Portfolio",
        rate_limiter: Union["RateLimiter", float, None] = None
    ):
        super().__init__("polymarket", real_client, clock, portfolio, rate_limiter)
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
        
        at_time = self._clock.current_time
        
        # Cap end_time at backtest time (wallet_pnl uses seconds) - modify in place first
        if 'end_time' in params:
            params['end_time'] = min(params['end_time'], at_time)
        else:
            params['end_time'] = at_time
        
        # Cap start_time if provided
        if 'start_time' in params:
            params['start_time'] = min(params['start_time'], at_time)
        
        # Now make a copy for the API call (API might modify it)
        params = params.copy()
        
        response = await self._call_api(self._real_api.wallet.get_wallet_pnl, params)
        
        # CRITICAL: Filter response data to remove PnL data points after backtest time
        # Wallet PnL has pnl_over_time array with timestamp fields (in seconds)
        if hasattr(response, 'pnl_over_time') and response.pnl_over_time:
            filtered_pnl = []
            for pnl_entry in response.pnl_over_time:
                # Get timestamp from PnL entry (field name: timestamp, in seconds)
                pnl_timestamp = None
                if hasattr(pnl_entry, 'timestamp'):
                    pnl_timestamp = pnl_entry.timestamp
                elif isinstance(pnl_entry, dict):
                    pnl_timestamp = pnl_entry.get('timestamp')
                
                # Only include PnL data points that occurred at or before backtest time
                if pnl_timestamp is not None and pnl_timestamp <= at_time:
                    filtered_pnl.append(pnl_entry)
            
            # Create filtered response
            try:
                import copy
                if hasattr(response, '__dict__'):
                    filtered_response = copy.copy(response)
                    filtered_response.pnl_over_time = filtered_pnl
                    # Also update end_time in response to match filtered data
                    if filtered_pnl:
                        filtered_response.end_time = min(
                            filtered_response.end_time if hasattr(filtered_response, 'end_time') else at_time,
                            at_time
                        )
                    return filtered_response
            except (AttributeError, TypeError):
                # Fallback if copy fails - create simple response object
                class FilteredResponse:
                    def __init__(self, pnl_over_time, granularity=None, start_time=None, end_time=None, wallet_address=None):
                        self.pnl_over_time = pnl_over_time
                        self.granularity = granularity
                        self.start_time = start_time
                        self.end_time = end_time
                        self.wallet_address = wallet_address
                return FilteredResponse(
                    filtered_pnl,
                    getattr(response, 'granularity', None),
                    getattr(response, 'start_time', None),
                    at_time,
                    getattr(response, 'wallet_address', None)
                )
        
        return response

