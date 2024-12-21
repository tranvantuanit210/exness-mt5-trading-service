from fastapi import APIRouter, HTTPException
from typing import List
from ..services.mt5_automation_service import MT5AutomationService
from ..models.automation import (
    ScheduledTrade, ConditionalOrder,
    GridTradingConfig, MartingaleConfig
)

def get_router(service: MT5AutomationService) -> APIRouter:
    router = APIRouter(prefix="/automation", tags=["Trading Automation"])

    @router.post("/schedule",
        summary="Schedule Trade",
        description="Schedule a trade for future execution")
    async def schedule_trade(trade: ScheduledTrade):
        """
        Schedule a trade with:
        - Execution time
        - Schedule type (once/daily/weekly/monthly)
        - Trading parameters
        - Optional conditions
        """
        try:
            result = await service.add_scheduled_trade(trade)
            return {"status": "success", "message": "Trade scheduled"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/conditional",
        summary="Create Conditional Order",
        description="Create order with multiple conditions")
    async def create_conditional_order(order: ConditionalOrder):
        """
        Create conditional order with:
        - Multiple conditions (price/indicator/time)
        - Trading parameters
        - Expiry settings
        """
        try:
            result = await service.add_conditional_order(order)
            return {"status": "success", "message": "Conditional order created"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/grid",
        summary="Setup Grid Trading",
        description="Configure and start grid trading")
    async def setup_grid_trading(config: GridTradingConfig):
        """
        Setup grid trading with:
        - Grid type and levels
        - Step size
        - Volume per level
        - Risk parameters
        """
        try:
            result = await service.setup_grid_trading(config)
            return {"status": "success", "message": "Grid trading setup completed"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/martingale",
        summary="Setup Martingale",
        description="Configure martingale trading strategy")
    async def setup_martingale(config: MartingaleConfig):
        """
        Setup martingale strategy with:
        - Initial volume
        - Multiplier
        - Maximum volume/trades
        - Reset conditions
        """
        try:
            result = await service.setup_martingale(config)
            return {"status": "success", "message": "Martingale strategy configured"}
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    return router 