from datetime import datetime
from typing import List
from decimal import Decimal
import MetaTrader5 as mt5
import logging
from .mt5_base_service import MT5BaseService
from ..models.trade import Position, TradeResponse, ModifyPositionRequest, OrderType
import asyncio
from tenacity import retry, stop_after_attempt, wait_exponential
from ..utils.retry_helper import handle_retry_error
from ..utils.constants import (
    MAX_RETRIES, VERIFICATION_WAIT_TIME, 
    TRADE_DEVIATION, TRADE_MAGIC,
    RETRY_MULTIPLIER, RETRY_MIN_WAIT, RETRY_MAX_WAIT
)

logger = logging.getLogger(__name__)

class MT5PositionService:
    """
    Service for managing trading positions in MT5.
    Provides functionality for retrieving, modifying, and closing positions,
    including risk management operations like hedging.
    """

    def __init__(self, base_service: MT5BaseService):
        """
        Initialize position service with base MT5 connection.
        
        Parameters:
        - base_service: Base MT5 service for connection management
        """
        self.base_service = base_service
        self.max_retries = MAX_RETRIES
        
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
            - Stop Loss
            - Take Profit
            - Current profit
            - Open time
            
        Note: Returns empty list if no positions or connection fails
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

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=RETRY_MULTIPLIER, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
        retry_error_callback=lambda retry_state: handle_retry_error(retry_state, max_retries=MAX_RETRIES)
    )
    async def modify_position(self, ticket: int, modify_request: ModifyPositionRequest) -> TradeResponse:
        """
        Modify Stop Loss and Take Profit levels with verification and retry mechanism
        
        Parameters:
        - ticket: Position ticket to modify
        - modify_request: New SL/TP levels
        
        Returns:
        - TradeResponse with modification result
        """
        if not await self.base_service.ensure_connected():
            return TradeResponse(order_id=ticket, symbol=None, status="error", message="Not connected to MT5")
        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return TradeResponse(
                    order_id=ticket,
                    symbol=None,
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
                    order_id=ticket,
                    symbol=position.symbol,
                    status="error",
                    message=f"Failed to modify position: {result.comment}"
                )

            # Add verification
            verified = await self._verify_position_modification(ticket, modify_request)
            if not verified:
                return TradeResponse(
                    order_id=ticket,
                    symbol=position.symbol,
                    status="error",
                    message="Position modification verification failed"
                )
            
            return TradeResponse(
                order_id=ticket,
                symbol=position.symbol,
                status="success",
                message="Position modified and verified successfully"
            )
        except Exception as e:
            logger.error(f"Error modifying position: {str(e)}")
            return TradeResponse(order_id=ticket, symbol=None, status="error", message=str(e))

    @retry(
        stop=stop_after_attempt(MAX_RETRIES),
        wait=wait_exponential(multiplier=RETRY_MULTIPLIER, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
        retry_error_callback=lambda retry_state: handle_retry_error(retry_state, max_retries=MAX_RETRIES)
    )
    async def close_position(self, ticket: int) -> TradeResponse:
        """
        Close a specific position with verification and retry mechanism
        
        Parameters:
        - ticket: Position ticket to close
        
        Returns:
        - TradeResponse with:
            - order_id: Closure order ticket (0 if failed)
            - status: Success/error status
            - message: Closure details or error message
        """
        if not await self.base_service.ensure_connected():
            return TradeResponse(
                order_id=ticket,
                symbol=None,
                status="error",
                message="Failed to connect to MT5"
            )
            
        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return TradeResponse(
                    order_id=ticket,
                    symbol=None,
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
                "deviation": TRADE_DEVIATION,
                "magic": TRADE_MAGIC,
                "comment": "python script close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return TradeResponse(
                    order_id=ticket,
                    symbol=position.symbol,
                    status="error",
                    message=f"Failed to close position: {result.comment}"
                )

            # Add verification
            verified = await self._verify_position_closure(ticket)
            if not verified:
                return TradeResponse(
                    order_id=ticket,
                    symbol=position.symbol,
                    status="error",
                    message="Position closure verification failed"
                )
                
            return TradeResponse(
                order_id=result.order,
                symbol=position.symbol,
                profit=Decimal(str(position.profit)),
                status="success",
                message="Position closed and verified successfully"
            )
            
        except Exception as e:
            logger.error(f"Error closing position: {str(e)}")
            return TradeResponse(
                order_id=ticket,
                symbol=None,
                status="error",
                message=str(e)
            )

    async def close_all_positions(self) -> List[TradeResponse]:
        """
        Close all currently open positions.
        
        Returns:
        - List[TradeResponse]: List of closure results for each position:
            - order_id: Closure order ticket
            - status: Success/error for each position
            - message: Individual closure details
            
        Note: Attempts to close all positions even if some fail
        """
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
        """
        Create a hedging position against an existing position.
        
        Parameters:
        - ticket: Original position ticket to hedge against
        
        Returns:
        - TradeResponse with:
            - order_id: New hedge position ticket (0 if failed)
            - status: Success/error status
            - message: Hedging details or error message
            
        Note: Creates opposite position with same volume to lock profit/loss
        """
        if not await self.base_service.ensure_connected():
            return TradeResponse(order_id=ticket, symbol=None, status="error", message="Not connected to MT5")
        try:
            position = mt5.positions_get(ticket=ticket)
            if not position:
                return TradeResponse(
                    order_id=ticket,
                    symbol=None,
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
                "deviation": TRADE_DEVIATION,
                "magic": TRADE_MAGIC,
                "comment": "python script hedge",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return TradeResponse(
                    order_id=ticket,
                    symbol=None,
                    status="error",
                    message=f"Failed to create hedge position: {result.comment}"
                )
            
            return TradeResponse(
                order_id=result.order,
                symbol=position.symbol,
                profit=Decimal(str(position.profit)),
                status="success",
                message="Hedge position created successfully"
            )
        except Exception as e:
            logger.error(f"Error creating hedge position: {str(e)}")
            return TradeResponse(order_id=ticket, symbol=None, status="error", message=str(e)) 

    async def _verify_position_closure(self, ticket: int) -> bool:
        """
        Verify that a position has been properly closed
        """
        try:
            await asyncio.sleep(VERIFICATION_WAIT_TIME)
            position = mt5.positions_get(ticket=ticket)
            if position:
                logger.error(f"Position {ticket} still exists after closure attempt")
                return False
            return True
        except Exception as e:
            logger.error(f"Error verifying position closure: {str(e)}")
            return False

    async def _verify_position_modification(self, ticket: int, modify_request: ModifyPositionRequest) -> bool:
        """
        Verify that position levels were properly modified
        """
        try:
            await asyncio.sleep(VERIFICATION_WAIT_TIME)
            position = mt5.positions_get(ticket=ticket)
            if not position:
                logger.error(f"Cannot find position with ticket {ticket}")
                return False
            position = position[0]
            if modify_request.stop_loss and position.sl != float(modify_request.stop_loss):
                logger.error("Stop Loss modification mismatch")
                return False
            if modify_request.take_profit and position.tp != float(modify_request.take_profit):
                logger.error("Take Profit modification mismatch")
                return False
            return True
        except Exception as e:
            logger.error(f"Error verifying position modification: {str(e)}")
            return False 