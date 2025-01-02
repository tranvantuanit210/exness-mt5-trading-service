from fastapi import APIRouter, HTTPException, Query
from typing import List
from datetime import datetime, timedelta, time, date
from ..services.mt5_signal_service import MT5SignalService
from ..services.mt5_notification_service import MT5NotificationService
from ..models.signal import TradingSignal, SignalType, TimeFrame, SymbolSignalsResponse, TimeframeSignal
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
        response_model=List[SymbolSignalsResponse],
        summary="Get Trading Signals",
        description="Get trading signals grouped by timestamp for multiple timeframes")
    async def get_signals_table(
        symbol: str = Query(..., description="Trading symbol (e.g. BTCUSD.P)"),
        timeframes: List[str] = Query(default=["1", "3", "5"], description="List of timeframes to display"),
        from_date: date = Query(
            default=date.today(),
            description="Start date (YYYY-MM-DD)"
        ),
        to_date: date = Query(
            default=date.today(),
            description="End date (YYYY-MM-DD)"
        )
    ):
        """
        Get signal table for a symbol with multiple timeframes.
        Returns data grouped by timestamp, each timestamp contains signals for different timeframes.
        If a timeframe has no data for a timestamp, it will be marked as NA.
        """
        try:
            # Convert dates to datetime with start and end of day
            from_datetime = datetime.combine(from_date, time.min)
            to_datetime = datetime.combine(to_date, time.max)

            signals = await signal_service.get_signals_by_symbol(
                symbol=symbol,
                timeframes=timeframes,
                from_date=from_datetime,
                to_date=to_datetime
            )

            # Group signals by timestamp
            grouped_signals = {}
            
            # First, get all unique timestamps from 1m timeframe
            one_minute_signals = [s for s in signals if s.timeframe.value == "1"]
            for signal in one_minute_signals:
                timestamp = signal.created_at.replace(second=0, microsecond=0)
                if timestamp not in grouped_signals:
                    grouped_signals[timestamp] = {
                        "symbol": signal.symbol,
                        "timestamp": timestamp,
                        "signals": {
                            # Initialize all timeframes with NA
                            tf: TimeframeSignal(
                                timeframe=tf,
                                signal_type=None,
                                entry_price=0.0
                            ) for tf in timeframes
                        }
                    }
            
            # Then fill in available signals for all timeframes
            for signal in signals:
                timestamp = signal.created_at.replace(second=0, microsecond=0)
                if timestamp in grouped_signals:  # Only update timestamps that exist in 1m data
                    grouped_signals[timestamp]["signals"][signal.timeframe.value] = TimeframeSignal(
                        timeframe=signal.timeframe.value,
                        signal_type=signal.signal_type,
                        entry_price=signal.entry_price
                    )

            # Sort results by timestamp descending
            result = [SymbolSignalsResponse(**data) for data in grouped_signals.values()]
            result.sort(key=lambda x: x.timestamp, reverse=True)

            return result

        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

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