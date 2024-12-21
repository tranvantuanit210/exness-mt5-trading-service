from typing import Optional
from decimal import Decimal
import MetaTrader5 as mt5
import logging
from .mt5_base_service import MT5BaseService
from ..models.trade import AccountInfo

logger = logging.getLogger(__name__)

class MT5AccountService:
    """
    Service for managing MT5 account information.
    Provides functionality for retrieving account details, balance, and margins.
    """

    def __init__(self, base_service: MT5BaseService):
        """
        Initialize account service with base MT5 connection.
        
        Parameters:
        - base_service: Base MT5 service for connection management
        """
        self.base_service = base_service

    async def get_account_info(self) -> Optional[AccountInfo]:
        """
        Get current account information and balance.
        
        Returns:
        - AccountInfo with:
            - Balance
            - Equity
            - Margin
            - Free margin
            - Number of open positions
        - None: If account info cannot be retrieved
        """
        if not await self.base_service.ensure_connected():
            return None
            
        try:
            account_info = mt5.account_info()
            if account_info is None:
                return None
                
            return AccountInfo(
                balance=Decimal(str(account_info.balance)),
                equity=Decimal(str(account_info.equity)),
                margin=Decimal(str(account_info.margin)),
                free_margin=Decimal(str(account_info.margin_free)),
                positions_count=mt5.positions_total(),
                profit=Decimal(str(account_info.profit)),
                leverage=account_info.leverage,
                currency=account_info.currency,
                name=account_info.name,
                server=account_info.server,
                trade_allowed=account_info.trade_allowed,
                limit_orders=account_info.limit_orders,
                margin_so_mode=account_info.margin_so_mode
            )
            
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            return None 