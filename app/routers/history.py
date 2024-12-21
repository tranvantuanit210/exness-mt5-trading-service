from fastapi import APIRouter
from typing import List
from ..services.mt5_history_service import MT5HistoryService
from ..models.trade import HistoricalOrder, HistoricalDeal, HistoricalPosition
from datetime import datetime

def get_router(service: MT5HistoryService) -> APIRouter:
    router = APIRouter(prefix="/history", tags=["Trading History"])

    @router.get("/orders",
        response_model=List[HistoricalOrder],
        summary="Get Order History",
        description="Retrieve historical orders within a specified date range")
    async def get_history_orders(
        start_date: datetime = None,
        end_date: datetime = None
    ):
        """
        Get historical orders data:
        - All executed and cancelled orders
        - Market and pending orders
        - Order execution details
        
        Parameters:
        - start_date: Starting date for history query (optional)
        - end_date: Ending date for history query (optional)
        
        Returns:
        - List of historical orders with full details:
            - Order ticket
            - Symbol
            - Type
            - Volume
            - Open/Close prices
            - Open/Close times
            - Profit/Loss
            - Comments
        """
        return await service.get_history_orders(start_date, end_date)

    @router.get("/deals",
        response_model=List[HistoricalDeal],
        summary="Get Deal History",
        description="Retrieve historical deals/trades within a specified date range")
    async def get_history_deals(
        start_date: datetime = None,
        end_date: datetime = None
    ):
        """
        Get historical deals data:
        - All executed trades
        - Entry and exit transactions
        - Profit/Loss details
        
        Parameters:
        - start_date: Starting date for history query (optional)
        - end_date: Ending date for history query (optional)
        
        Returns:
        - List of historical deals with full details:
            - Deal ticket
            - Order ticket
            - Symbol
            - Type (buy/sell)
            - Volume
            - Price
            - Commission
            - Swap
            - Profit
            - Time
        """
        return await service.get_history_deals(start_date, end_date)

    @router.get("/positions",
        response_model=List[HistoricalPosition],
        summary="Get Position History",
        description="Retrieve historical positions within a specified date range")
    async def get_history_positions(
        start_date: datetime = None,
        end_date: datetime = None
    ):
        """
        Get historical positions data:
        - All closed positions
        - Position lifecycle details
        - Full profit/loss analysis
        
        Parameters:
        - start_date: Starting date for history query (optional)
        - end_date: Ending date for history query (optional)
        
        Returns:
        - List of historical positions with full details:
            - Position ticket
            - Symbol
            - Type (long/short)
            - Volume
            - Entry/Exit prices
            - Open/Close times
            - Stop Loss/Take Profit
            - Swap
            - Commission
            - Total profit/loss
        """
        return await service.get_history_positions(start_date, end_date)

    return router 