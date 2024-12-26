from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum
from typing import Optional

class SignalType(str, Enum):
    UP = "UP"
    DOWN = "DOWN"

class TimeFrame(str, Enum):
    M1 = "M1"    # 1 minute (60 seconds)
    M5 = "M5"    # 5 minutes (300 seconds)
    M15 = "M15"  # 15 minutes (900 seconds)
    M30 = "M30"  # 30 minutes (1800 seconds)
    H1 = "H1"    # 1 hour (3600 seconds)
    H4 = "H4"    # 4 hours (14400 seconds)
    D1 = "D1"    # 1 day (86400 seconds)
    W1 = "W1"    # 1 week (604800 seconds)
    MN1 = "MN1"  # 1 month (average 2592000 seconds)

class TradingSignal(BaseModel):
    id: Optional[str] = Field(None, alias="_id")  # MongoDB's _id field
    symbol: str
    signal_type: SignalType
    timeframe: TimeFrame
    entry_price: float
    created_at: datetime = datetime.now()

    class Config:
        allow_population_by_field_name = True  # Allow both _id and id 