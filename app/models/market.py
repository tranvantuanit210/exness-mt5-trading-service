from pydantic import BaseModel
from datetime import datetime
from decimal import Decimal

class SymbolInfo(BaseModel):
    name: str
    bid: Decimal
    ask: Decimal
    spread: int
    digits: int
    trade_mode: str
    trade_allowed: bool
    volume_min: Decimal
    volume_max: Decimal
    volume_step: Decimal

class TickData(BaseModel):
    time: datetime
    bid: Decimal
    ask: Decimal
    last: Decimal
    volume: Decimal

class OHLC(BaseModel):
    time: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal 

class Symbol(BaseModel):
    name: str
    description: str
    path: str
    point: float
    digits: int