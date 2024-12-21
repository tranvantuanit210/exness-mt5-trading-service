from pydantic import BaseModel
from typing import List, Dict, Optional
from datetime import datetime

class TradeStats(BaseModel):
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    avg_profit: float
    roi: float
    period: str  # daily/weekly/monthly
    start_date: datetime
    end_date: datetime

class PairAnalysis(BaseModel):
    symbol: str
    total_profit: float
    total_trades: int
    win_rate: float
    avg_spread: float
    best_trading_hours: List[int]
    risk_score: float

class DrawdownInfo(BaseModel):
    current_drawdown: float
    max_drawdown: float
    drawdown_periods: List[Dict[str, datetime]]
    recovery_time: Optional[int]
    risk_level: str

class PeriodicReport(BaseModel):
    period: str
    start_date: datetime
    end_date: datetime
    account_balance: float
    net_profit: float
    total_trades: int
    win_rate: float
    top_pairs: List[PairAnalysis]
    drawdown_info: DrawdownInfo 