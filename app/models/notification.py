from pydantic import BaseModel, Field
from typing import Optional, List
from decimal import Decimal
from datetime import datetime
from enum import Enum

class NotificationChannel(str, Enum):
    TELEGRAM = "telegram"
    DISCORD = "discord"

class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class AlertType(str, Enum):
    SIGNAL = "signal"  # Tín hiệu giao dịch
    PNL = "pnl"       # Cảnh báo lãi/lỗ
    NEWS = "news"     # Tin tức thị trường
    PRICE = "price"   # Biến động giá

class PriceAlert(BaseModel):
    symbol: str
    condition: str = Field(..., description="above/below/cross")
    price_level: Decimal
    channels: List[NotificationChannel]
    
class PnLAlert(BaseModel):
    position_id: Optional[int] = None  # None = toàn bộ portfolio
    profit_threshold: Optional[Decimal] = None
    loss_threshold: Optional[Decimal] = None
    channels: List[NotificationChannel]

class SignalAlert(BaseModel):
    symbol: str
    signal_type: str  # buy/sell/close
    entry_price: Decimal
    stop_loss: Optional[Decimal]
    take_profit: Optional[Decimal]
    confidence: Optional[float]
    channels: List[NotificationChannel]

class NewsAlert(BaseModel):
    symbols: List[str]
    importance: List[str] = ["high", "medium", "low"]
    channels: List[NotificationChannel]

class NotificationConfig(BaseModel):
    telegram_token: Optional[str]
    telegram_chat_id: Optional[str]
    discord_webhook: Optional[str]