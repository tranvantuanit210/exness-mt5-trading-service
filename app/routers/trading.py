from fastapi import APIRouter, HTTPException, Depends
from ..services.mt5_trading_service import MT5TradingService
from ..services.mt5_notification_service import MT5NotificationService
from ..models.trade import OrderType, TradeRequest, TradeResponse

def get_router(
    trading_service: MT5TradingService,
    notification_service: MT5NotificationService
) -> APIRouter:
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
            result = await trading_service.execute_market_order(trade_request)
            
            if result.status == "success":
                await notification_service.send_telegram(
                    f"🎯 New Market Order\n\n"
                    f"Symbol: {trade_request.symbol}\n"
                    f"Type: {'BUY' if trade_request.order_type == OrderType.BUY else 'SELL'}\n"
                    f"Volume: {trade_request.calculated_volume}\n"
                    f"Ticket: {result.order_id}\n"
                    f"✅ Status: Success"
                )
            else:
                await notification_service.send_telegram(
                    f"❌ Market Order Failed\n\n"
                    f"Symbol: {trade_request.symbol}\n"
                    f"Error: {result.message}"
                )

            if result.status == "error":
                raise HTTPException(status_code=400, detail=result.message)
            return result
            
        except Exception as e:
            await notification_service.send_telegram(
                f"❌ Trading Error\n\n"
                f"Details: {str(e)}"
            )
            raise HTTPException(status_code=500, detail=str(e))

    return router