from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from enum import Enum
from decimal import Decimal
from datetime import datetime

class OrderType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

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
    profit: Decimal = Field(..., description="Current profit")
    leverage: int = Field(..., description="Account leverage")
    currency: str = Field(..., description="Account currency")
    name: str = Field(..., description="Account name")
    server: str = Field(..., description="Trading server")
    trade_allowed: bool = Field(..., description="Trading allowed flag")
    limit_orders: int = Field(..., description="Maximum allowed orders")
    margin_so_mode: int = Field(..., description="Margin SO mode")

class TradeRequest(BaseModel):
    symbol: str = Field(
        ..., 
        description="Trading symbol (e.g., BTCUSDm, XAUUSD, BTCUSD)"
    )
    order_type: OrderType = Field(
        ..., 
        description="Order type (BUY: open buy position, SELL: open sell position)"
    )
    amount: float = Field(
        ..., 
        description="Investment amount in deposit currency (e.g., 1000 USD)",
        gt=0
    )
    stop_loss: Optional[float] = Field(
        None, 
        description="Stop loss price level. Leave empty for no stop loss"
    )
    take_profit: Optional[float] = Field(
        None, 
        description="Take profit price level. Leave empty for no take profit"
    )
    comment: Optional[str] = Field(
        None, 
        description="Order comment or note",
        max_length=100
    )
    calculated_volume: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "symbol": "BTCUSDm",
                "order_type": "BUY",
                "amount": 1000,
                "stop_loss": 1.0800,
                "take_profit": 1.0900,
                "comment": "Python trading bot order"
            }
        }

class TradeResponse(BaseModel):
    order_id: int = Field(..., description="Order ID from MT5")
    status: str = Field(..., description="Order status (success/error)")
    message: str = Field(..., description="Detailed message") 
    symbol: Optional[str] = Field(None, description="Trading symbol")
    profit: Optional[Decimal] = Field(None, description="Profit")

class PendingOrder(BaseModel):
    ticket: int
    symbol: str
    type: str
    volume: Decimal
    price: Decimal
    stop_loss: Optional[Decimal]
    take_profit: Optional[Decimal]
    comment: Optional[str]

class HistoricalOrder(BaseModel):
    ticket: int
    symbol: str
    type: str
    volume: Decimal
    price: Decimal
    time: datetime
    state: int
    profit: Optional[Decimal] = None

class HistoricalDeal(BaseModel):
    ticket: int
    order_ticket: int
    symbol: str
    type: str
    volume: Decimal
    price: Decimal
    time: datetime
    profit: Decimal

class HistoricalPosition(BaseModel):
    ticket: int
    symbol: str
    type: str
    volume: Decimal
    open_price: Decimal
    close_price: Decimal
    open_time: datetime
    close_time: datetime
    profit: Decimal

class ModifyPositionRequest(BaseModel):
    stop_loss: Optional[Decimal]
    take_profit: Optional[Decimal] 

class ModifyTradeRequest(BaseModel):
    stop_loss: Optional[Decimal] = Field(None, description="New stop loss level")
    take_profit: Optional[Decimal] = Field(None, description="New take profit level")

    class Config:
        json_schema_extra = {
            "example": {
                "stop_loss": 1.0800,
                "take_profit": 1.0900
            }
        }