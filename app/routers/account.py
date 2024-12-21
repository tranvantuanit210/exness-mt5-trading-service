from fastapi import APIRouter, Depends
from typing import Optional
from ..services.mt5_account_service import MT5AccountService
from ..models.trade import AccountInfo

def get_router(service: MT5AccountService) -> APIRouter:
    router = APIRouter(prefix="/account", tags=["Account Information"])

    @router.get("/info", 
        response_model=Optional[AccountInfo],
        summary="Get Account Information",
        description="Retrieve detailed trading account information and balance")
    async def get_account_info():
        """
        Get account information including:
        - Balance
        - Equity
        - Margin
        - Free margin
        - Number of open positions
        """
        return await service.get_account_info()

    return router 