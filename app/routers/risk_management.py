from fastapi import APIRouter, HTTPException
from typing import List
from ..services.mt5_position_service import MT5PositionService
from ..models.trade import TradeResponse, ModifyPositionRequest

def get_router(service: MT5PositionService) -> APIRouter:
    router = APIRouter(prefix="/risk", tags=["Risk Management"])

    @router.post("/positions/{ticket}/modify",
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
        result = await service.modify_position(ticket, modify_request)
        if result.status == "error":
            raise HTTPException(status_code=400, detail=result.message)
        return result

    @router.post("/positions/close-all",
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
        return await service.close_all_positions()

    @router.post("/positions/hedge/{ticket}",
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
        result = await service.create_hedge_position(ticket)
        if result.status == "error":
            raise HTTPException(status_code=400, detail=result.message)
        return result

    return router 