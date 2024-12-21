from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum
from decimal import Decimal
from datetime import datetime

class OrderType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderStatus(str, Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

class Position(BaseModel):
    ticket: int = Field(..., description="Position ticket/order ID")
    symbol: str = Field(..., description="Trading symbol")
    order_type: OrderType = Field(..., description="Order type (BUY/SELL)")
    volume: Decimal = Field(..., description="Trading volume")
    open_price: Decimal = Field(..., description="Position open price")
    stop_loss: Optional[Decimal] = Field(None, description="Stop loss level")
    take_profit: Optional[Decimal] = Field(None, description="Take profit level")
    profit: Decimal = Field(..., description="Current profit")
    open_time: datetime = Field(..., description="Position open time")

class AccountInfo(BaseModel):
    balance: Decimal = Field(..., description="Account balance")
    equity: Decimal = Field(..., description="Account equity")
    margin: Decimal = Field(..., description="Used margin")
    free_margin: Decimal = Field(..., description="Free margin")
    positions_count: int = Field(..., description="Number of open positions")

class TradeRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol (e.g., EURUSD)")
    order_type: OrderType = Field(..., description="Order type (BUY/SELL)")
    volume: Decimal = Field(..., gt=0, description="Trading volume")
    stop_loss: Optional[Decimal] = Field(None, description="Stop loss level")
    take_profit: Optional[Decimal] = Field(None, description="Take profit level")

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "EURUSD",
                "order_type": "BUY",
                "volume": 0.1,
                "stop_loss": 1.0800,
                "take_profit": 1.0900
            }
        }

class TradeResponse(BaseModel):
    order_id: int = Field(..., description="Order ID from MT5")
    status: str = Field(..., description="Order status (success/error)")
    message: str = Field(..., description="Detailed message") 