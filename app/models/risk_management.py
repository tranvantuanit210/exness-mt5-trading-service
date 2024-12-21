from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional, List

class PositionSizeRequest(BaseModel):
    symbol: str = Field(..., description="Trading symbol")
    risk_percent: Decimal = Field(..., gt=0, le=100, description="Risk percentage of account balance")
    entry_price: Decimal = Field(..., description="Planned entry price")
    stop_loss: Decimal = Field(..., description="Planned stop loss level")
    
class PositionSizeResponse(BaseModel):
    position_size: Decimal = Field(..., description="Calculated position size in lots")
    risk_amount: Decimal = Field(..., description="Amount at risk in account currency")
    pip_value: Decimal = Field(..., description="Value per pip in account currency")
    stop_loss_pips: int = Field(..., description="Distance to stop loss in pips")

class TrailingStopRequest(BaseModel):
    ticket: int = Field(..., description="Position ticket number")
    trail_points: int = Field(..., gt=0, description="Trail distance in points")
    step_points: Optional[int] = Field(None, gt=0, description="Step size for trailing")

class PortfolioRiskRequest(BaseModel):
    max_total_risk: Decimal = Field(..., gt=0, le=100, description="Maximum total portfolio risk %")
    correlation_threshold: Optional[Decimal] = Field(0.7, description="Correlation threshold for risk adjustment")

class PortfolioRiskResponse(BaseModel):
    total_risk_percent: Decimal = Field(..., description="Current total portfolio risk")
    position_risks: List[dict] = Field(..., description="Risk details for each position")
    correlated_pairs: List[dict] = Field(..., description="Highly correlated position pairs")
    risk_status: str = Field(..., description="Overall risk status (OK/WARNING/DANGER)") 