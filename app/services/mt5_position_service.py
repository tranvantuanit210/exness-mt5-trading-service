from datetime import datetime
from typing import List
from decimal import Decimal
import MetaTrader5 as mt5
import logging
from .mt5_base_service import MT5BaseService
from ..models.trade import Position, TradeResponse, ModifyPositionRequest, OrderType

logger = logging.getLogger(__name__)

class MT5PositionService:
    def __init__(self, base_service: MT5BaseService):
        self.base_service = base_service

    async def get_positions(self) -> List[Position]:
        """Get all open positions"""
        if not await self.base_service.ensure_connected():
            return []
            
        try:
            positions = mt5.positions_get()
            if positions is None:
                return []
                
            result = []
            for pos in positions:
                result.append(Position(
                    ticket=pos.ticket,
                    symbol=pos.symbol,
                    order_type=OrderType.BUY if pos.type == mt5.ORDER_TYPE_BUY else OrderType.SELL,
                    volume=Decimal(str(pos.volume)),
                    open_price=Decimal(str(pos.price_open)),
                    stop_loss=Decimal(str(pos.sl)) if pos.sl else None,
                    take_profit=Decimal(str(pos.tp)) if pos.tp else None,
                    profit=Decimal(str(pos.profit)),
                    open_time=datetime.fromtimestamp(pos.time)
                ))
            return result
            
        except Exception as e:
            logger.error(f"Error getting positions: {str(e)}")
            return []

    async def modify_position(self, ticket: int, modify_request: ModifyPositionRequest) -> TradeResponse:
        """Modify position's SL/TP"""
        if not await self.base_service.ensure_connected():
            return TradeResponse(order_id=0, status="error", message="Not connected to MT5")
        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return TradeResponse(
                    order_id=0,
                    status="error",
                    message=f"Position {ticket} not found"
                )
            
            position = position[0]
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "symbol": position.symbol,
                "sl": float(modify_request.stop_loss) if modify_request.stop_loss else position.sl,
                "tp": float(modify_request.take_profit) if modify_request.take_profit else position.tp
            }
            
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return TradeResponse(
                    order_id=0,
                    status="error",
                    message=f"Failed to modify position: {result.comment}"
                )
            
            return TradeResponse(
                order_id=ticket,
                status="success",
                message="Position modified successfully"
            )
        except Exception as e:
            logger.error(f"Error modifying position: {str(e)}")
            return TradeResponse(order_id=0, status="error", message=str(e))

    async def close_position(self, ticket: int) -> TradeResponse:
        """Close specific position by ticket"""
        if not await self.base_service.ensure_connected():
            return TradeResponse(
                order_id=0,
                status="error",
                message="Failed to connect to MT5"
            )
            
        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return TradeResponse(
                    order_id=0,
                    status="error",
                    message=f"Position {ticket} not found"
                )
                
            position = position[0]
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "symbol": position.symbol,
                "volume": float(position.volume),
                "type": mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                "price": mt5.symbol_info_tick(position.symbol).bid if position.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(position.symbol).ask,
                "deviation": 20,
                "magic": 234000,
                "comment": "python script close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return TradeResponse(
                    order_id=0,
                    status="error",
                    message=f"Failed to close position: {result.comment}"
                )
                
            return TradeResponse(
                order_id=result.order,
                status="success",
                message="Position closed successfully"
            )
            
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            return TradeResponse(
                order_id=0,
                status="error",
                message=str(e)
            )

    async def close_all_positions(self) -> List[TradeResponse]:
        """Close all open positions"""
        if not await self.base_service.ensure_connected():
            return []
        try:
            positions = await self.get_positions()
            results = []
            for position in positions:
                result = await self.close_position(position.ticket)
                results.append(result)
            return results
        except Exception as e:
            logger.error(f"Error closing all positions: {str(e)}")
            return []

    async def create_hedge_position(self, ticket: int) -> TradeResponse:
        """Create hedge position"""
        if not await self.base_service.ensure_connected():
            return TradeResponse(order_id=0, status="error", message="Not connected to MT5")
        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return TradeResponse(
                    order_id=0,
                    status="error",
                    message=f"Position {ticket} not found"
                )
            
            position = position[0]
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": position.symbol,
                "volume": float(position.volume),
                "type": mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY,
                "price": mt5.symbol_info_tick(position.symbol).ask if position.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(position.symbol).bid,
                "deviation": 20,
                "magic": 234000,
                "comment": "python script hedge",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return TradeResponse(
                    order_id=0,
                    status="error",
                    message=f"Failed to create hedge position: {result.comment}"
                )
            
            return TradeResponse(
                order_id=result.order,
                status="success",
                message="Hedge position created successfully"
            )
        except Exception as e:
            logger.error(f"Error creating hedge position: {str(e)}")
            return TradeResponse(order_id=0, status="error", message=str(e)) 