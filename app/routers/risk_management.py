from fastapi import APIRouter, HTTPException
from typing import List
from ..services.mt5_risk_service import MT5RiskService
from ..models.risk_management import (
    PositionSizeRequest, PositionSizeResponse,
    TrailingStopRequest, PortfolioRiskRequest, PortfolioRiskResponse
)

def get_router(service: MT5RiskService) -> APIRouter:
    router = APIRouter(prefix="/risk", tags=["Risk Management"])

    @router.post("/position-size",
        response_model=PositionSizeResponse,
        summary="Calculate Position Size",
        description="Calculate optimal position size based on risk parameters")
    async def calculate_position_size(request: PositionSizeRequest):
        """
        Calculate optimal position size based on:
        - Account risk percentage
        - Entry price
        - Stop loss level
        - Symbol specifications
        """
        try:
            return await service.calculate_position_size(request)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/trailing-stop",
        summary="Manage Trailing Stop",
        description="Set or update trailing stop loss for a position")
    async def manage_trailing_stop(request: TrailingStopRequest):
        """
        Manage trailing stop loss with:
        - Trail distance
        - Optional step size
        - Position ticket
        """
        result = await service.manage_trailing_stop(request)
        if not result:
            raise HTTPException(status_code=400, detail="Failed to update trailing stop")
        return {"status": "success", "message": "Trailing stop updated"}

    @router.post("/portfolio-risk",
        response_model=PortfolioRiskResponse,
        summary="Analyze Portfolio Risk",
        description="Analyze total portfolio risk and position correlations")
    async def analyze_portfolio_risk(request: PortfolioRiskRequest):
        """
        Analyze portfolio risk including:
        - Total risk exposure
        - Individual position risks
        - Correlated positions
        - Risk status assessment
        """
        try:
            return await service.analyze_portfolio_risk(request)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return router 