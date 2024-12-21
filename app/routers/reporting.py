from fastapi import APIRouter, Depends, HTTPException
from typing import List
from datetime import datetime, timedelta
from ..services.mt5_reporting_service import MT5ReportingService
from ..models.reporting import TradeStats, PairAnalysis, DrawdownInfo, PeriodicReport

def get_router(reporting_service: MT5ReportingService) -> APIRouter:
    router = APIRouter(prefix="/reporting", tags=["Reporting"])

    @router.get("/performance", response_model=TradeStats)
    async def get_performance_stats(
        period: str,
        start_date: datetime = None,
        end_date: datetime = None
    ):
        """Get trading performance statistics"""
        if not start_date:
            start_date = datetime.now() - timedelta(days=30)
        if not end_date:
            end_date = datetime.now()
        
        return await reporting_service.get_performance_stats(start_date, end_date, period)

    @router.get("/pair/{symbol}", response_model=PairAnalysis)
    async def analyze_pair(
        symbol: str,
        period: int = 30
    ):
        """Analyze trading performance for specific symbol"""
        return await reporting_service.analyze_pair(symbol, period)

    @router.get("/drawdown", response_model=DrawdownInfo)
    async def get_drawdown_info():
        """Get current drawdown information"""
        return await reporting_service.monitor_drawdown()

    @router.get("/report/{period}", response_model=PeriodicReport)
    async def get_periodic_report(
        period: str
    ):
        """Generate periodic report (daily/weekly/monthly)"""
        if period not in ['daily', 'weekly', 'monthly']:
            raise HTTPException(status_code=400, detail="Invalid period")
        return await reporting_service.generate_periodic_report(period)

    return router 