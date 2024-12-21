from fastapi import APIRouter, HTTPException
from typing import List
from ..services.mt5_order_service import MT5OrderService
from ..models.trade import TradeRequest, TradeResponse, PendingOrder

def get_router(service: MT5OrderService) -> APIRouter:
    router = APIRouter(prefix="/orders", tags=["Orders Management"])

    @router.get("/pending",
        response_model=List[PendingOrder],
        summary="Get Pending Orders",
        description="Retrieve all pending orders currently placed in the trading account")
    async def get_pending_orders():
        """
        Returns list of all pending orders with:
        - Order ticket
        - Symbol
        - Type (Buy Limit, Sell Limit, Buy Stop, Sell Stop)
        - Volume
        - Open price
        - Stop Loss
        - Take Profit
        - Comment
        - Creation time
        """
        return await service.get_pending_orders()

    @router.post("/pending",
        response_model=TradeResponse,
        summary="Create Pending Order",
        description="Place a new pending order with specified parameters")
    async def create_pending_order(order: TradeRequest):
        """
        Create a new pending order with:
        - Symbol to trade
        - Order type (Buy Limit, Sell Limit, Buy Stop, Sell Stop)
        - Volume
        - Price level to trigger the order
        - Optional Stop Loss
        - Optional Take Profit
        - Optional comment
        
        Returns:
        - Order ticket if successful
        - Error message if failed
        """
        result = await service.place_pending_order(order)
        if result.status == "error":
            raise HTTPException(status_code=400, detail=result.message)
        return result

    @router.delete("/pending/{ticket}",
        response_model=TradeResponse,
        summary="Cancel Pending Order",
        description="Cancel an existing pending order by its ticket number")
    async def cancel_pending_order(ticket: int):
        """
        Cancel a pending order by ticket number
        
        Parameters:
        - ticket: The unique identifier of the pending order
        
        Returns:
        - Success message if cancelled
        - Error message if failed or order not found
        """
        result = await service.cancel_pending_order(ticket)
        if result.status == "error":
            raise HTTPException(status_code=400, detail=result.message)
        return result

    return router 