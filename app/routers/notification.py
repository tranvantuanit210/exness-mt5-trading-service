from fastapi import APIRouter, HTTPException
from typing import List
from ..services.mt5_notification_service import MT5NotificationService
from ..models.notification import (
    NotificationConfig, PriceAlert, PnLAlert,
    SignalAlert, NewsAlert
)

def get_router(service: MT5NotificationService) -> APIRouter:
    router = APIRouter(prefix="/notifications", tags=["Notifications"])

    @router.post("/config",
        summary="Configure Notification Settings",
        description="Set up notification channels and credentials")
    async def configure_notifications(config: NotificationConfig):
        """
        Configure notification settings:
        - Telegram credentials
        - Email settings
        - Webhook URLs
        - Other channel configs
        """
        try:
            await service.initialize(config)
            return {"status": "success", "message": "Notification settings updated"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/alerts/price",
        summary="Add Price Alert",
        description="Create new price level alert")
    async def add_price_alert(alert: PriceAlert):
        """
        Add price alert with:
        - Symbol
        - Price level
        - Condition (above/below/cross)
        - Notification channels
        """
        try:
            result = await service.add_price_alert(alert)
            return {"status": "success", "message": "Price alert added"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/alerts/pnl",
        summary="Add P&L Alert",
        description="Create new profit/loss threshold alert")
    async def add_pnl_alert(alert: PnLAlert):
        """
        Add P&L alert with:
        - Position ID (optional)
        - Profit threshold
        - Loss threshold
        - Notification channels
        """
        try:
            result = await service.add_pnl_alert(alert)
            return {"status": "success", "message": "P&L alert added"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/alerts/news",
        summary="Add News Alert",
        description="Create new market news alert")
    async def add_news_alert(alert: NewsAlert):
        """
        Add news alert with:
        - Symbols to monitor
        - News importance levels
        - Notification channels
        """
        try:
            result = await service.add_news_alert(alert)
            return {"status": "success", "message": "News alert added"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/signal",
        summary="Send Signal Notification",
        description="Send trading signal notification")
    async def send_signal(signal: SignalAlert):
        """
        Send trading signal with:
        - Symbol
        - Signal type
        - Entry price
        - Stop loss/Take profit
        - Confidence level
        """
        try:
            await service.send_signal_notification(signal)
            return {"status": "success", "message": "Signal notification sent"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/test",
        summary="Test Notification System",
        description="Send a test message to verify notification setup")
    async def test_notification():
        """
        Send test notification to verify:
        - Telegram connection
        - Bot permissions
        - Message formatting
        """
        try:
            await service.send_telegram(
                "🔔 <b>MT5 Trading</b>\n\n"
                "✅ Connection Successful!\n"
                "✅ Bot Permissions OK\n"
                "✅ Channel Configuration OK\n\n"
                "You will receive trading alerts in this channel."
            )
            return {
                "status": "success", 
                "message": "Test notification sent successfully"
            }
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to send test notification: {str(e)}"
            )

    return router 