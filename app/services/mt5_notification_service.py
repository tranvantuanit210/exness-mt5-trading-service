import logging
import aiohttp
from typing import List, Dict, Any, Optional
from decimal import Decimal
from datetime import datetime
import asyncio
from .mt5_base_service import MT5BaseService
from ..models.notification import (
    NotificationChannel, NotificationPriority, AlertType,
    PriceAlert, PnLAlert, SignalAlert, NewsAlert, NotificationConfig
)

logger = logging.getLogger(__name__)

class MT5NotificationService:
    def __init__(self, base_service: MT5BaseService):
        self.base_service = base_service
        self.config: NotificationConfig = None
        self.price_alerts: List[PriceAlert] = []
        self.pnl_alerts: List[PnLAlert] = []
        self.news_alerts: List[NewsAlert] = []
        
    async def initialize(self, config: NotificationConfig):
        """Initialize notification service with config"""
        self.config = config
        
    async def send_telegram(self, message: str, priority: NotificationPriority = NotificationPriority.MEDIUM):
        """Send message via Telegram"""
        if not self.config or not self.config.telegram_token:
            logger.warning("Telegram not configured")
            return False
            
        try:
            url = f"https://api.telegram.org/bot{self.config.telegram_token}/sendMessage"
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json={
                    "chat_id": self.config.telegram_chat_id,
                    "text": message,
                    "parse_mode": "HTML"
                }) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Telegram notification error: {str(e)}")
            return False

    async def send_discord(self, message: str, priority: NotificationPriority = NotificationPriority.MEDIUM):
        """Send message via Discord webhook"""
        if not self.config or not self.config.discord_webhook:
            logger.warning("Discord not configured")
            return False
            
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.config.discord_webhook, json={
                    "content": message
                }) as response:
                    return response.status == 204
        except Exception as e:
            logger.error(f"Discord notification error: {str(e)}")
            return False

    async def add_price_alert(self, alert: PriceAlert):
        """Add new price alert"""
        self.price_alerts.append(alert)
        return True

    async def add_pnl_alert(self, alert: PnLAlert):
        """Add new P&L alert"""
        self.pnl_alerts.append(alert)
        return True

    async def add_news_alert(self, alert: NewsAlert):
        """Add new news alert"""
        self.news_alerts.append(alert)
        return True

    async def check_price_alerts(self):
        """Check and trigger price alerts"""
        if not await self.base_service.ensure_connected():
            return
            
        for alert in self.price_alerts:
            current_price = await self._get_current_price(alert.symbol)
            if self._check_price_condition(current_price, alert.condition, alert.price_level):
                message = (
                    f"🔔 Price Alert\n"
                    f"Symbol: {alert.symbol}\n"
                    f"Condition: {alert.condition}\n"
                    f"Level: {alert.price_level}\n"
                    f"Current Price: {current_price}"
                )
                await self._send_notifications(message, alert.channels)

    async def check_pnl_alerts(self):
        """Check and trigger P&L alerts"""
        if not await self.base_service.ensure_connected():
            return
            
        for alert in self.pnl_alerts:
            current_pnl = await self._get_position_pnl(alert.position_id)
            if self._check_pnl_thresholds(current_pnl, alert):
                message = (
                    f"💰 P&L Alert\n"
                    f"Position: {alert.position_id or 'Portfolio'}\n"
                    f"Current P&L: {current_pnl}\n"
                    f"Threshold Hit: {'Profit' if current_pnl > 0 else 'Loss'}"
                )
                await self._send_notifications(message, alert.channels)

    async def send_signal_notification(self, signal: SignalAlert):
        """Send trading signal notification"""
        message = (
            f"📊 Trading Signal\n"
            f"Symbol: {signal.symbol}\n"
            f"Type: {signal.signal_type.upper()}\n"
            f"Entry: {signal.entry_price}\n"
            f"SL: {signal.stop_loss or 'N/A'}\n"
            f"TP: {signal.take_profit or 'N/A'}\n"
            f"Confidence: {signal.confidence or 'N/A'}"
        )
        await self._send_notifications(message, signal.channels)

    async def _send_notifications(self, message: str, channels: List[NotificationChannel]):
        """Send notification to multiple channels"""
        tasks = []
        for channel in channels:
            if channel == NotificationChannel.TELEGRAM:
                tasks.append(self.send_telegram(message))
            elif channel == NotificationChannel.DISCORD:
                tasks.append(self.send_discord(message))
                
        await asyncio.gather(*tasks)

    async def _get_current_price(self, symbol: str) -> Decimal:
        """Get current price for symbol"""
        # Implementation depends on your MT5 service
        pass

    async def _get_position_pnl(self, position_id: Optional[int]) -> Decimal:
        """Get P&L for position or portfolio"""
        # Implementation depends on your MT5 service
        pass

    def _check_price_condition(self, current: Decimal, condition: str, level: Decimal) -> bool:
        """Check if price condition is met"""
        if condition == "above":
            return current > level
        elif condition == "below":
            return current < level
        elif condition == "cross":
            # Implement crossing logic
            pass
        return False

    def _check_pnl_thresholds(self, current_pnl: Decimal, alert: PnLAlert) -> bool:
        """Check if P&L thresholds are breached"""
        if alert.profit_threshold and current_pnl >= alert.profit_threshold:
            return True
        if alert.loss_threshold and current_pnl <= alert.loss_threshold:
            return True
        return False 