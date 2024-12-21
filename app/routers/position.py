from fastapi import APIRouter, HTTPException
from typing import List
from ..services.mt5_position_service import MT5PositionService
from ..models.trade import TradeResponse, Position, ModifyPositionRequest

def get_router(position_service: MT5PositionService) -> APIRouter:
    router = APIRouter(prefix="/positions", tags=["Position Management"])

    @router.get("/",
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
        return await position_service.get_positions()

    @router.delete("/{ticket}",
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
        result = await position_service.close_position(ticket)
        if result.status == "error":
            raise HTTPException(status_code=400, detail=result.message)
        return result

    @router.post("/{ticket}/modify",
        response_model=TradeResponse,
        summary="Modify Position Levels",
        description="Modify Stop Loss and Take Profit levels for an existing position")
    async def modify_position(
        ticket: int,
        modify_request: ModifyPositionRequest
    ):
        """
        Modify risk management levels for a position:
        - Update Stop Loss level
        - Update Take Profit level
        
        Parameters:
        - ticket: Position ticket number
        - modify_request: New SL/TP levels
        
        Returns:
        - Success confirmation if modified
        - Error message if modification failed
        """
        result = await position_service.modify_position(ticket, modify_request)
        if result.status == "error":
            raise HTTPException(status_code=400, detail=result.message)
        return result

    @router.post("/close-all",
        response_model=List[TradeResponse],
        summary="Close All Positions",
        description="Close all currently open positions in the trading account")
    async def close_all_positions():
        """
        Close all open positions:
        - Attempts to close every open position
        - Returns results for each position
        
        Returns:
        - List of results for each position closure
        - Success/failure status for each position
        - Error messages for failed closures
        """
        return await position_service.close_all_positions()

    @router.post("/hedge/{ticket}",
        response_model=TradeResponse,
        summary="Create Hedge Position",
        description="Create a hedging position against an existing position")
    async def create_hedge_position(ticket: int):
        """
        Create a hedge position:
        - Opens opposite position with same volume
        - Helps to lock in current profit/loss
        
        Parameters:
        - ticket: Original position ticket to hedge against
        
        Returns:
        - New hedge position details if successful
        - Error message if hedging failed
        """
        result = await position_service.create_hedge_position(ticket)
        if result.status == "error":
            raise HTTPException(status_code=400, detail=result.message)
        return result

    return router 