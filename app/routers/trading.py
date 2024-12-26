from fastapi import APIRouter, HTTPException
from ..services.mt5_trading_service import MT5TradingService
from ..models.trade import TradeRequest, TradeResponse

def get_router(service: MT5TradingService) -> APIRouter:
    router = APIRouter(prefix="/trading", tags=["Basic Trading"])

    @router.post("/market-order",
        response_model=TradeResponse,
        summary="Execute Market Order",
        description="Execute an immediate market order for buying or selling")
    async def execute_trade(trade_request: TradeRequest):
        """
        Execute a market order with:
        - Symbol to trade
        - Order type (Buy or Sell)
        - Amount (lot size)
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
            result = await service.execute_market_order(trade_request)
            if result.status == "error":
                raise HTTPException(status_code=400, detail=result.message)
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    return router