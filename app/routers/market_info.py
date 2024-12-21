from fastapi import APIRouter, HTTPException
from typing import List
from ..services.mt5_market_service import MT5MarketService
from ..models.market import Symbol, SymbolInfo, TickData, OHLC

def get_router(service: MT5MarketService) -> APIRouter:
    router = APIRouter(prefix="/market", tags=["Market Information"])

    @router.get("/symbols",
        response_model=List[Symbol],
        summary="Get Available Symbols",
        description="Retrieve a list of all available trading symbols with their basic information")
    async def get_symbols() -> List[Symbol]:
        """
        Returns list of available trading symbols with:
        - Symbol name
        - Description
        - Path in symbol tree
        - Point value
        - Decimal digits
        """
        return await service.get_symbols()

    @router.get("/symbols/{symbol}/info",
        response_model=SymbolInfo,
        summary="Get Symbol Details",
        description="Get detailed market information for a specific symbol including pricing and trading conditions")
    async def get_symbol_info(symbol: str):
        """
        Get detailed symbol information including:
        - Current bid/ask prices
        - Spread
        - Trading mode and permissions
        - Minimum and maximum volumes
        - Volume step
        """
        info = await service.get_symbol_info(symbol)
        if not info:
            raise HTTPException(status_code=404, detail=f"Symbol {symbol} not found")
        return info

    @router.get("/symbols/{symbol}/price",
        summary="Get Current Price",
        description="Get real-time price information for a specific symbol")
    async def get_symbol_price(symbol: str):
        """
        Get current price data including:
        - Bid price
        - Ask price
        - Last trade price
        """
        price = await service.get_symbol_price(symbol)
        if not price:
            raise HTTPException(status_code=404, detail=f"Price not available for {symbol}")
        return price

    @router.get("/symbols/{symbol}/ticks",
        response_model=List[TickData],
        summary="Get Tick History",
        description="Retrieve historical tick data for a specific symbol")
    async def get_symbol_ticks(
        symbol: str,
        count: int = 100
    ):
        """
        Get historical tick data with:
        - Timestamp
        - Bid/Ask prices
        - Last trade price
        - Volume
        
        Parameters:
        - symbol: Trading symbol name
        - count: Number of ticks to retrieve (default: 100)
        """
        return await service.get_symbol_ticks(symbol, count)

    @router.get("/symbols/{symbol}/ohlc",
        response_model=List[OHLC],
        summary="Get Candlestick Data",
        description="Retrieve OHLC (candlestick) data for a specific symbol and timeframe")
    async def get_symbol_ohlc(
        symbol: str,
        timeframe: str = "M1",
        count: int = 100
    ):
        """
        Get candlestick (OHLC) data with:
        - Timestamp
        - Open price
        - High price
        - Low price
        - Close price
        - Volume
        
        Parameters:
        - symbol: Trading symbol name
        - timeframe: Time period (M1, M5, M15, M30, H1, H4, D1)
        - count: Number of candles to retrieve (default: 100)
        """
        return await service.get_symbol_ohlc(symbol, timeframe, count)

    return router 