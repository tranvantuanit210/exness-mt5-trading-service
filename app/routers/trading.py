from fastapi import APIRouter, HTTPException
from typing import List, Optional
from ..services.mt5_trading_service import MT5TradingService
from ..models.trade import TradeRequest, TradeResponse, Position, AccountInfo, ModifyTradeRequest

def get_router(service: MT5TradingService) -> APIRouter:
    router = APIRouter(prefix="/trading", tags=["Basic Trading"])

    @router.post("/execute",
        response_model=TradeResponse,
        summary="Execute Market Order",
        description="Execute an immediate market order for buying or selling")
    async def execute_trade(trade_request: TradeRequest):
        """
        Execute a market order with:
        - Symbol to trade
        - Order type (Buy or Sell)
        - Volume (lot size)
        - Optional Stop Loss
        - Optional Take Profit
        - Optional comment
        
        Parameters:
        - trade_request: Trading order details
        
        Returns:
        - Order ticket and execution details if successful
        - Error message if execution failed
        """
        try:
            result = await service.execute_trade(trade_request)
            if result.status == "error":
                raise HTTPException(status_code=400, detail=result.message)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/positions",
        response_model=List[Position],
        summary="Get Open Positions",
        description="Retrieve all currently open positions in the trading account")
    async def get_positions():
        """
        Get all open positions with details:
        - Position ticket
        - Symbol
        - Type (long/short)
        - Volume
        - Open price
        - Current price
        - Stop Loss
        - Take Profit
        - Swap
        - Profit/Loss
        - Comment
        """
        return await service.get_positions()

    @router.get("/account",
        response_model=Optional[AccountInfo],
        summary="Get Account Information",
        description="Retrieve detailed trading account information and balance")
    async def get_account_info():
        """
        Get account information including:
        - Account number
        - Balance
        - Equity
        - Margin
        - Free margin
        - Margin level
        - Leverage
        - Currency
        - Server name
        - Company
        """
        info = await service.get_account_info()
        if info is None:
            raise HTTPException(status_code=500, detail="Failed to get account info")
        return info

    @router.delete("/positions/{ticket}",
        response_model=TradeResponse,
        summary="Close Position",
        description="Close a specific open position by its ticket number")
    async def close_position(ticket: int):
        """
        Close an open position:
        - Closes entire position volume
        - Calculates final profit/loss
        
        Parameters:
        - ticket: Position ticket to close
        
        Returns:
        - Closure confirmation and P/L if successful
        - Error message if closure failed
        """
        result = await service.close_position(ticket)
        if result.status == "error":
            raise HTTPException(status_code=400, detail=result.message)
        return result

    @router.put("/positions/{ticket}/levels",
        response_model=TradeResponse,
        summary="Modify Trade Levels",
        description="Update Stop Loss and Take Profit levels for an open position")
    async def modify_trade_levels(ticket: int, modify_request: ModifyTradeRequest):
        """
        Modify trade's SL/TP levels:
        - Update Stop Loss level
        - Update Take Profit level
        - Both levels are optional
        
        Parameters:
        - ticket: Position ticket to modify
        - modify_request: New SL/TP levels
        
        Returns:
        - Modification confirmation if successful
        - Error message if modification failed
        """
        result = await service.modify_trade_levels(ticket, modify_request)
        if result.status == "error":
            raise HTTPException(status_code=400, detail=result.message)
        return result

    return router