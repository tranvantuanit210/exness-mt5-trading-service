from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from ..services.mt5_market_service import MT5MarketService
from ..models.market import SymbolInfo, TickData, OHLC, SymbolList

def get_router(market_service: MT5MarketService) -> APIRouter:
    router = APIRouter(prefix="/market", tags=["Market Info"])

    @router.get("/symbols", response_model=SymbolList,
        summary="Get and Search Symbols",
        description="Get all trading symbols or search with optional filters")
    async def search_symbols(
        search: Optional[str] = Query(None, description="Search term (e.g., 'BTC', 'GOLD', 'USD')")
    ):
        """
        Get all symbols or search with filters
        
        Examples:
        - /market/symbols - Get all symbols
        - /market/symbols?search=btc - Search for Bitcoin related symbols
        - /market/symbols?search=gold - Search for Gold related symbols
        - /market/symbols?search=usd - Search for USD currency pairs
        """
        symbols = await market_service.search_symbols(search)
        return SymbolList(symbols=symbols)

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
        info = await market_service.get_symbol_info(symbol)
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
        price = await market_service.get_symbol_price(symbol)
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
        """
        return await market_service.get_symbol_ticks(symbol, count)

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
        """
        return await market_service.get_symbol_ohlc(symbol, timeframe, count)

    return router 