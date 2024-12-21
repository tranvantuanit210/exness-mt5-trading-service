from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union
from decimal import Decimal
from datetime import datetime, time
from enum import Enum

class ScheduleType(str, Enum):
    ONCE = "once"          # Execute trade once
    DAILY = "daily"        # Execute trade daily
    WEEKLY = "weekly"      # Execute trade weekly
    MONTHLY = "monthly"    # Execute trade monthly

class ConditionType(str, Enum):
    PRICE = "price"        # Price condition
    INDICATOR = "indicator"# Technical indicator condition
    TIME = "time"          # Time condition
    VOLUME = "volume"      # Volume condition

class GridType(str, Enum):
    SYMMETRIC = "symmetric"    # Equal distance grid levels
    ASCENDING = "ascending"    # Increasing distance grid levels
    DESCENDING = "descending"  # Decreasing distance grid levels

class MartingaleType(str, Enum):
    CLASSIC = "classic"        # Double position size after loss
    ANTI = "anti"             # Double position size after win
    FIBONACCI = "fibonacci"    # Use Fibonacci sequence for sizing

class TradeCondition(BaseModel):
    type: ConditionType
    operator: str = Field(..., description=">, <, =, >=, <=")
    value: Union[float, str]
    indicator_params: Optional[Dict] = None

class ScheduledTrade(BaseModel):
    symbol: str
    schedule_type: ScheduleType
    execution_time: time
    order_type: str = Field(..., description="BUY/SELL")
    volume: Decimal
    stop_loss: Optional[Decimal]
    take_profit: Optional[Decimal]
    conditions: Optional[List[TradeCondition]]
    expiry_date: Optional[datetime]
    max_trades: Optional[int]

class ConditionalOrder(BaseModel):
    symbol: str
    conditions: List[TradeCondition]
    order_type: str
    volume: Decimal
    stop_loss: Optional[Decimal]
    take_profit: Optional[Decimal]
    expiry: Optional[datetime]

class GridTradingConfig(BaseModel):
    symbol: str
    grid_type: GridType
    start_price: Decimal
    step_size: Decimal
    grid_levels: int
    volume_per_level: Decimal
    take_profit_pips: Optional[int]
    stop_loss_pips: Optional[int]
    max_positions: Optional[int]

class MartingaleConfig(BaseModel):
    symbol: str
    martingale_type: MartingaleType
    initial_volume: Decimal
    multiplier: Decimal = Field(2.0, description="Volume multiplier after loss/win")
    max_volume: Optional[Decimal]
    max_trades: Optional[int]
    reset_on_win: bool = True 