from typing import List, Optional
from decimal import Decimal
from datetime import datetime
import MetaTrader5 as mt5
import logging
from .mt5_base_service import MT5BaseService
from ..models.trade import HistoricalOrder, HistoricalDeal, HistoricalPosition

logger = logging.getLogger(__name__)

class MT5HistoryService:
    """
    Service for retrieving historical trading data from MT5.
    Provides functionality for accessing historical orders, deals, and positions
    within specified date ranges.
    """

    def __init__(self, base_service: MT5BaseService):
        """
        Initialize history service with base MT5 connection.
        
        Parameters:
        - base_service: Base MT5 service for connection management
        """
        self.base_service = base_service

    async def get_history_orders(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[HistoricalOrder]:
        """
        Get historical orders within specified date range.
        
        Parameters:
        - start_date: Starting date for history query (optional)
        - end_date: Ending date for history query (optional)
        
        Returns:
        - List[HistoricalOrder]: List of historical orders with details:
            - Order ticket
            - Symbol traded
            - Order type (market/pending)
            - Volume
            - Open price
            - Opening time
            - Order state
            - Profit/Loss
            
        Note: Returns all history if dates not specified
        """
        if not await self.base_service.ensure_connected():
            return []
        try:
            orders = mt5.history_orders_get(start_date, end_date)
            return [
                HistoricalOrder(
                    ticket=order.ticket,
                    symbol=order.symbol,
                    type="buy" if order.type == mt5.ORDER_TYPE_BUY else "sell",
                    volume=Decimal(str(order.volume_current)),
                    price=Decimal(str(order.price_open)),
                    time=datetime.fromtimestamp(order.time_setup),
                    state=order.state,
                    profit=Decimal(str(order.profit)) if hasattr(order, 'profit') and order.profit is not None else None
                ) for order in orders
            ] if orders else []
        except Exception as e:
            logger.error(f"Error getting history orders: {str(e)}")
            return []

    async def get_history_deals(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[HistoricalDeal]:
        """
        Get historical deals/trades within specified date range.
        
        Parameters:
        - start_date: Starting date for history query (optional)
        - end_date: Ending date for history query (optional)
        
        Returns:
        - List[HistoricalDeal]: List of historical deals with details:
            - Deal ticket
            - Related order ticket
            - Symbol traded
            - Deal type (buy/sell)
            - Volume
            - Price
            - Execution time
            - Profit/Loss
            
        Note: Returns all history if dates not specified
        """
        if not await self.base_service.ensure_connected():
            return []
        try:
            deals = mt5.history_deals_get(start_date, end_date)
            return [
                HistoricalDeal(
                    ticket=deal.ticket,
                    order_ticket=deal.order,
                    symbol=deal.symbol,
                    type="buy" if deal.type == mt5.ORDER_TYPE_BUY else "sell",
                    volume=Decimal(str(deal.volume)),
                    price=Decimal(str(deal.price)),
                    time=datetime.fromtimestamp(deal.time),
                    profit=Decimal(str(deal.profit))
                ) for deal in deals
            ] if deals else []
        except Exception as e:
            logger.error(f"Error getting history deals: {str(e)}")
            return []

    async def get_history_positions(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[HistoricalPosition]:
        """
        Get historical closed positions within specified date range.
        
        Parameters:
        - start_date: Starting date for history query (optional)
        - end_date: Ending date for history query (optional)
        
        Returns:
        - List[HistoricalPosition]: List of historical positions with details:
            - Position ticket
            - Symbol traded
            - Position type (long/short)
            - Volume
            - Entry price
            - Exit price
            - Opening time
            - Closing time
            - Final profit/loss
            
        Note: 
        - Returns all history if dates not specified
        - Reconstructs position history from deals
        - Only includes fully closed positions
        """
        if not await self.base_service.ensure_connected():
            return []
        try:
            # Get closed positions through deals
            deals = mt5.history_deals_get(start_date, end_date)
            if not deals:
                return []

            positions = {}
            for deal in deals:
                if deal.entry == mt5.DEAL_ENTRY_IN:  # Position open
                    positions[deal.position_id] = {
                        "ticket": deal.position_id,
                        "symbol": deal.symbol,
                        "type": "buy" if deal.type == mt5.ORDER_TYPE_BUY else "sell",
                        "volume": Decimal(str(deal.volume)),
                        "open_price": Decimal(str(deal.price)),
                        "open_time": datetime.fromtimestamp(deal.time),
                        "close_price": None,
                        "close_time": None,
                        "profit": Decimal("0")
                    }
                elif deal.entry == mt5.DEAL_ENTRY_OUT:  # Position close
                    if deal.position_id in positions:
                        positions[deal.position_id].update({
                            "close_price": Decimal(str(deal.price)),
                            "close_time": datetime.fromtimestamp(deal.time),
                            "profit": Decimal(str(deal.profit))
                        })

            return [
                HistoricalPosition(**pos)
                for pos in positions.values()
                if pos["close_time"] is not None
            ]
        except Exception as e:
            logger.error(f"Error getting position history: {str(e)}")
            return [] 