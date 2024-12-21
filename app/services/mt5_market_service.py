from typing import List, Optional, Dict
from decimal import Decimal
from datetime import datetime
import MetaTrader5 as mt5
import logging
from .mt5_base_service import MT5BaseService
from ..models.market import Symbol, SymbolInfo, TickData, OHLC

logger = logging.getLogger(__name__)

class MT5MarketService:
    def __init__(self, base_service: MT5BaseService):
        self.base_service = base_service

    async def get_symbols(self) -> List[Symbol]:
        """Get all available trading symbols"""
        if not await self.base_service.ensure_connected():
            return []
            
        symbols = mt5.symbols_get()
        if symbols is None:
            return []
        
        result = []
        for symbol in symbols:
            result.append(Symbol(
                name=symbol.name,
                description=symbol.description,
                path=symbol.path,
                point=symbol.point,
                digits=symbol.digits
            ))
            
        return result

    async def get_symbol_info(self, symbol: str) -> Optional[SymbolInfo]:
        """Get detailed information about a symbol"""
        if not await self.base_service.ensure_connected():
            return None
        try:
            info = mt5.symbol_info(symbol)
            if info is None:
                return None
            return SymbolInfo(
                name=info.name,
                bid=Decimal(str(info.bid)),
                ask=Decimal(str(info.ask)),
                spread=info.spread,
                digits=info.digits,
                trade_mode=info.trade_mode,
                trade_allowed=info.trade_allowed,
                volume_min=Decimal(str(info.volume_min)),
                volume_max=Decimal(str(info.volume_max)),
                volume_step=Decimal(str(info.volume_step))
            )
        except Exception as e:
            logger.error(f"Error getting symbol info: {str(e)}")
            return None

    async def get_symbol_price(self, symbol: str) -> Optional[Dict[str, Decimal]]:
        """Get current price for a symbol"""
        if not await self.base_service.ensure_connected():
            return None
        try:
            tick = mt5.symbol_info_tick(symbol)
            if tick is None:
                return None
            return {
                "bid": Decimal(str(tick.bid)),
                "ask": Decimal(str(tick.ask)),
                "last": Decimal(str(tick.last))
            }
        except Exception as e:
            logger.error(f"Error getting symbol price: {str(e)}")
            return None

    async def get_symbol_ticks(self, symbol: str, count: int) -> List[TickData]:
        """Get tick history for a symbol"""
        if not await self.base_service.ensure_connected():
            return []
        try:
            ticks = mt5.copy_ticks_from(symbol, datetime.now(), count, mt5.COPY_TICKS_ALL)
            return [
                TickData(
                    time=datetime.fromtimestamp(tick[0]),
                    bid=Decimal(str(tick[1])),
                    ask=Decimal(str(tick[2])),
                    last=Decimal(str(tick[3])),
                    volume=Decimal(str(tick[4]))
                ) for tick in ticks
            ] if ticks is not None else []
        except Exception as e:
            logger.error(f"Error getting symbol ticks: {str(e)}")
            return []

    async def get_symbol_ohlc(self, symbol: str, timeframe: str, count: int) -> List[OHLC]:
        """Get candlestick data"""
        if not await self.base_service.ensure_connected():
            return []
        try:
            timeframe_map = {
                "M1": mt5.TIMEFRAME_M1,
                "M5": mt5.TIMEFRAME_M5,
                "M15": mt5.TIMEFRAME_M15,
                "M30": mt5.TIMEFRAME_M30,
                "H1": mt5.TIMEFRAME_H1,
                "H4": mt5.TIMEFRAME_H4,
                "D1": mt5.TIMEFRAME_D1,
            }
            tf = timeframe_map.get(timeframe, mt5.TIMEFRAME_M1)
            rates = mt5.copy_rates_from_pos(symbol, tf, 0, count)
            return [
                OHLC(
                    time=datetime.fromtimestamp(rate[0]),
                    open=Decimal(str(rate[1])),
                    high=Decimal(str(rate[2])),
                    low=Decimal(str(rate[3])),
                    close=Decimal(str(rate[4])),
                    volume=Decimal(str(rate[5]))
                ) for rate in rates
            ] if rates is not None else []
        except Exception as e:
            logger.error(f"Error getting OHLC data: {str(e)}")
            return []