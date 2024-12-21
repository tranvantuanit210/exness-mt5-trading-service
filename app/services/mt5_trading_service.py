from typing import List, Optional, Dict, Any
from decimal import Decimal
from datetime import datetime
import MetaTrader5 as mt5
import logging
from .mt5_base_service import MT5BaseService
from ..models.trade import (
    TradeRequest, TradeResponse, Position, AccountInfo,
    OrderType, ModifyTradeRequest
)

logger = logging.getLogger(__name__)

class MT5TradingService:
    """
    Service for handling trading operations in MT5.
    Provides functionality for executing trades, managing positions and account information.
    """

    def __init__(self, base_service: MT5BaseService):
        """
        Initialize trading service with base MT5 connection.
        
        Parameters:
        - base_service: Base MT5 service for connection management
        """
        self.base_service = base_service

    @property
    def initialized(self):
        """Check if trading service is initialized and connected"""
        return self.base_service.initialized

    def _prepare_trade_request(self, trade_request: TradeRequest) -> Dict[str, Any]:
        """
        Prepare trade request parameters for MT5 API.
        
        Parameters:
        - trade_request: Trading request with order details
        
        Returns:
        - Dict containing formatted request parameters for MT5 API
        
        Raises:
        - ValueError: If symbol information cannot be retrieved
        """
        tick = mt5.symbol_info_tick(trade_request.symbol)
        if tick is None:
            raise ValueError(f"Cannot get symbol info for {trade_request.symbol}")
            
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": trade_request.symbol,
            "volume": float(trade_request.volume),
            "type": (mt5.ORDER_TYPE_BUY 
                    if trade_request.order_type == OrderType.BUY 
                    else mt5.ORDER_TYPE_SELL),
            "price": tick.ask if trade_request.order_type == OrderType.BUY else tick.bid,
            "deviation": 20,
            "magic": 234000,
            "comment": "python script order",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        if trade_request.stop_loss:
            request["sl"] = float(trade_request.stop_loss)
        if trade_request.take_profit:
            request["tp"] = float(trade_request.take_profit)
            
        return request

    async def execute_trade(self, trade_request: TradeRequest) -> TradeResponse:
        """
        Execute a market order with specified parameters.
        
        Parameters:
        - trade_request: Trade request containing:
            - Symbol to trade
            - Order type (buy/sell)
            - Volume
            - Optional stop loss
            - Optional take profit
        
        Returns:
        - TradeResponse with:
            - order_id: Executed order ticket (0 if failed)
            - status: 'success' or 'error'
            - message: Success/error details
        """
        if not await self.base_service.ensure_connected():
            return TradeResponse(
                order_id=0,
                status="error",
                message="Failed to connect to MT5"
            )

        try:
            request = self._prepare_trade_request(trade_request)
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed: {result.comment}")
                return TradeResponse(
                    order_id=0,
                    status="error",
                    message=f"Order failed: {result.comment}"
                )

            logger.info(f"Order placed successfully: Order ID {result.order}")
            return TradeResponse(
                order_id=result.order,
                status="success",
                message="Order placed successfully"
            )

        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return TradeResponse(
                order_id=0,
                status="error",
                message=str(e)
            )

    async def get_positions(self) -> List[Position]:
        """
        Get all currently open positions.
        
        Returns:
        - List[Position]: List of open positions with details:
            - Ticket number
            - Symbol
            - Type (buy/sell)
            - Volume
            - Open price
            - Stop loss
            - Take profit
            - Current profit
            - Open time
        """
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

    async def close_position(self, ticket: int) -> TradeResponse:
        """
        Close a specific position by its ticket number.
        
        Parameters:
        - ticket: Position ticket to close
        
        Returns:
        - TradeResponse with:
            - order_id: Closure order ticket
            - status: Success/error
            - message: Closure details
        """
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

    async def modify_trade_levels(self, ticket: int, modify_request: ModifyTradeRequest) -> TradeResponse:
        """
        Modify stop loss and take profit levels for an open position.
        
        Parameters:
        - ticket: Position ticket to modify
        - modify_request: New SL/TP levels
        
        Returns:
        - TradeResponse with modification result
        """
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
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "symbol": position.symbol,
            }
            
            # Only include SL/TP if they are provided
            if modify_request.stop_loss is not None:
                request["sl"] = float(modify_request.stop_loss)
            if modify_request.take_profit is not None:
                request["tp"] = float(modify_request.take_profit)
            
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return TradeResponse(
                    order_id=0,
                    status="error",
                    message=f"Failed to modify trade levels: {result.comment}"
                )
                
            return TradeResponse(
                order_id=ticket,
                status="success",
                message="Trade levels modified successfully"
            )
            
        except Exception as e:
            logger.error(f"Error modifying trade levels: {str(e)}")
            return TradeResponse(
                order_id=0,
                status="error",
                message=str(e)
            ) 