from pydantic import BaseModel
from typing import List
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

# New models for symbol search
class SearchSymbolInfo(BaseModel):
    name: str
    description: str
    base_currency: str
    profit_currency: str
    trade_contract_size: float
    minimum_volume: float
    maximum_volume: float
    volume_step: float
    category: str
    current_price: float
    minimum_amount_usd: float
    amount_step_usd: float
    bid: float
    ask: float
    spread: float

class SymbolList(BaseModel):
    symbols: List[SearchSymbolInfo]