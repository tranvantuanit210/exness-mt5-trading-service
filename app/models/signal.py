from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional

class SignalType(str, Enum):
    UP = "UP"
    DOWN = "DOWN"

class TimeFrame(str, Enum):
    S1 = "S"      # 1 second
    S5 = "5S"     # 5 seconds  
    S15 = "15S"   # 15 seconds
    S30 = "30S"   # 30 seconds
    M1 = "1"      # 1 minute
    M3 = "3"      # 3 minutes
    M5 = "5"      # 5 minutes
    M15 = "15"    # 15 minutes
    M30 = "30"    # 30 minutes
    M45 = "45"    # 45 minutes
    H1 = "60"     # 1 hour
    H2 = "120"    # 2 hours
    H3 = "180"    # 3 hours
    H4 = "240"    # 4 hours
    D1 = "D"      # 1 day
    D5 = "5D"     # 5 days
    W1 = "W"      # 1 week
    MN1 = "M"     # 1 month
    Q1 = "3M"     # 1 quarter (3 months)
    Y1 = "12M"    # 1 year

class TradingSignal(BaseModel):
    _id: Optional[str] = None
    symbol: str = Field(..., description="Trading symbol (e.g. BTCUSDT)")
    signal_type: SignalType = Field(..., description="Signal type: UP or DOWN")
    timeframe: TimeFrame = Field(..., description="Trading timeframe")
    entry_price: float = Field(..., description="Entry price for the signal")
    created_at: datetime = Field(default_factory=datetime.now, description="Signal creation timestamp")

    class Config:
        populate_by_name = True
        json_schema_extra = {
            "example": {
                "_id": "67763f3f90a1c1a9b9bb8851",
                "symbol": "BTCUSDT",
                "signal_type": "UP",
                "timeframe": "S",
                "entry_price": 0.0,
                "created_at": "2025-01-02T14:21:12.172Z"
            }
        } 

class TimeframeSignal(BaseModel):
    timeframe: str
    signal_type: Optional[SignalType] = None
    entry_price: float

class SymbolSignalsResponse(BaseModel):
    symbol: str
    timestamp: datetime
    signals: dict[str, TimeframeSignal]  # key là timeframe (e.g., "1m", "3m", "5m") 