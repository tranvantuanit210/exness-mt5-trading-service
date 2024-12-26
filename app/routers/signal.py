from fastapi import APIRouter, HTTPException
from typing import List, Optional
from datetime import datetime
from ..services.mt5_signal_service import MT5SignalService
from ..services.mt5_notification_service import MT5NotificationService
from ..models.signal import TradingSignal, SignalType, TimeFrame
from ..utils.display_formats import get_timeframe_display

def get_router(
    signal_service: MT5SignalService,
    notification_service: MT5NotificationService
) -> APIRouter:
    router = APIRouter(prefix="/signals", tags=["Trading Signals"])

    @router.post("/",
        summary="Add Trading Signal",
        description="Save a new trading signal")
    async def add_signal(signal: TradingSignal):
        """Add new trading signal with market direction"""
        try:
            result = await signal_service.add_signal(signal)
            
            # Send notification
            direction = "🔼" if signal.signal_type == SignalType.UP else "🔽"
            await notification_service.send_telegram(
                f"{direction} New Trading Signal\n\n"
                f"Symbol: {signal.symbol}\n"
                f"Direction: {"UP" if signal.signal_type == SignalType.UP else "DOWN"}\n"
                f"Timeframe: {get_timeframe_display(signal.timeframe)}\n"
                f"Price: {signal.entry_price}\n"
                f"✅ Status: Saved"
            )
            
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @router.get("/",
        response_model=List[TradingSignal],
        summary="Get Trading Signals",
        description="Retrieve trading signals with optional filters")
    async def get_signals(
        symbol: Optional[str] = None,
        timeframe: Optional[TimeFrame] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ):
        """Get trading signals with filters"""
        return await signal_service.get_signals(
            symbol, timeframe, start_date, end_date, limit
        )

    @router.delete("/{signal_id}",
        summary="Delete Trading Signal",
        description="Delete a specific trading signal")
    async def delete_signal(signal_id: str):
        """Delete trading signal by ID"""
        result = await signal_service.delete_signal(signal_id)
        if result["status"] == "error":
            raise HTTPException(status_code=404, detail=result["message"])
        return result

    return router 