from fastapi import APIRouter, HTTPException, Depends
from typing import List
from ..services.mt5_position_service import MT5PositionService
from ..services.mt5_notification_service import MT5NotificationService
from ..models.trade import TradeResponse, Position, ModifyPositionRequest

def get_router(
    position_service: MT5PositionService,
    notification_service: MT5NotificationService
) -> APIRouter:
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
        try:
            result = await position_service.close_position(ticket)
            
            if result.status == "success":
                await notification_service.send_telegram(
                    f"🔴 Position Closed\n\n"
                    f"Close Ticket: {ticket}\n"
                    f"Symbol: {result.symbol}\n"
                    f"Profit: {result.profit}\n"
                    f"✅ Status: Success"
                )
            else:
                await notification_service.send_telegram(
                    f"❌ Position Close Failed\n\n"
                    f"Ticket: {ticket}\n"
                    f"Symbol: {result.symbol}\n"
                    f"Error: {result.message}"
                )

            if result.status == "error":
                raise HTTPException(status_code=400, detail=result.message)
            return result
            
        except Exception as e:
            await notification_service.send_telegram(
                f"❌ Position Close Error\n\n"
                f"Ticket: {ticket}\n"
                f"Symbol: {result.symbol}\n"
                f"Details: {str(e)}"
            )
            raise HTTPException(status_code=400, detail=str(e))

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
        try:
            result = await position_service.modify_position(ticket, modify_request)
            
            if result.status == "success":
                await notification_service.send_telegram(
                    f"📝 Position Modified\n\n"
                    f"Modify Ticket: {ticket}\n"
                    f"Symbol: {result.symbol}\n"
                    f"Stop Loss: {modify_request.stop_loss}\n"
                    f"Take Profit: {modify_request.take_profit}\n"
                    f"Profit: {result.profit}\n"
                    f"✅ Status: Success"
                )
            else:
                await notification_service.send_telegram(
                    f"❌ Position Modify Failed\n\n"
                    f"Ticket: {ticket}\n"
                    f"Symbol: {result.symbol}\n"
                    f"Error: {result.message}"
                )

            if result.status == "error":
                raise HTTPException(status_code=400, detail=result.message)
            return result
            
        except Exception as e:
            await notification_service.send_telegram(
                f"❌ Position Modify Error\n\n"
                f"Ticket: {ticket}\n"
                f"Symbol: {result.symbol}\n"
                f"Details: {str(e)}"
            )
            raise HTTPException(status_code=400, detail=str(e))

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
        try:
            results = await position_service.close_all_positions()
            
            success_count = len([r for r in results if r.status == "success"])
            success_tickets = [f"{r.order_id} ({r.symbol} {r.profit})" for r in results if r.status == "success"]    
            
            await notification_service.send_telegram(
                f"🔴 All Positions Closed\n\n"
                f"Positions Closed: {success_count}\n"
                f"Close Tickets: {', '.join(map(str, success_tickets))}\n"
                f"✅ Status: Complete"
            )
            
            return results
            
        except Exception as e:
            await notification_service.send_telegram(
                f"❌ Close All Positions Error\n\n"
                f"Details: {str(e)}"
            )
            raise HTTPException(status_code=500, detail=str(e))

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