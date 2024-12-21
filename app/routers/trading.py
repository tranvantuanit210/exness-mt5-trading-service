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

    return router