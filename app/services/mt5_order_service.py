from typing import Any, Dict, List, Optional
from decimal import Decimal
import MetaTrader5 as mt5
import logging
from .mt5_base_service import MT5BaseService
from ..models.trade import TradeRequest, TradeResponse, PendingOrder, OrderType
from ..utils.constants import TRADE_DEVIATION, TRADE_MAGIC

logger = logging.getLogger(__name__)

class MT5OrderService:
    """
    Service for managing pending orders in MT5.
    Provides functionality for creating, retrieving and cancelling pending orders.
    """

    def __init__(self, base_service: MT5BaseService):
        """
        Initialize order service with base MT5 connection.
        
        Parameters:
        - base_service: Base MT5 service for connection management
        """
        self.base_service = base_service

    def _prepare_trade_request(self, trade_request: TradeRequest) -> Dict[str, Any]:
        """
        Prepare pending order request parameters for MT5 API.
        
        Parameters:
        - trade_request: Trading request with order details
        
        Returns:
        - Dict containing formatted request parameters for MT5 API
        
        Raises:
        - ValueError: If symbol information cannot be retrieved
        
        Note: Differs from market order preparation by using TRADE_ACTION_PENDING
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
            "deviation": TRADE_DEVIATION,
            "magic": TRADE_MAGIC,
            "comment": "python script order",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        if trade_request.stop_loss:
            request["sl"] = float(trade_request.stop_loss)
        if trade_request.take_profit:
            request["tp"] = float(trade_request.take_profit)
            
        return request

    async def get_pending_orders(self) -> List[PendingOrder]:
        """
        Get list of all pending orders.
        
        Returns:
        - List[PendingOrder]: List of pending orders with details:
            - Ticket number
            - Symbol
            - Type (buy/sell limit/stop)
            - Volume
            - Price
            - Stop Loss
            - Take Profit
            - Comment
            
        Note: Returns empty list if no pending orders or connection fails
        """
        if not await self.base_service.ensure_connected():
            return []
        try:
            orders = mt5.orders_get()
            return [
                PendingOrder(
                    ticket=order.ticket,
                    symbol=order.symbol,
                    type=order.type,
                    volume=Decimal(str(order.volume_current)),
                    price=Decimal(str(order.price_open)),
                    stop_loss=Decimal(str(order.sl)) if order.sl else None,
                    take_profit=Decimal(str(order.tp)) if order.tp else None,
                    comment=order.comment
                ) for order in orders
            ] if orders else []
        except Exception as e:
            logger.error(f"Error getting pending orders: {str(e)}")
            return []

    async def place_pending_order(self, order: TradeRequest) -> TradeResponse:
        """
        Create a new pending order.
        
        Parameters:
        - order: Trade request containing:
            - Symbol
            - Order type (buy/sell limit/stop)
            - Volume
            - Price level
            - Optional Stop Loss
            - Optional Take Profit
        
        Returns:
        - TradeResponse with:
            - order_id: Created order ticket (0 if failed)
            - status: 'success' or 'error'
            - message: Creation details or error message
        """
        if not await self.base_service.ensure_connected():
            return TradeResponse(order_id=0, status="error", message="Not connected to MT5")
        try:
            request = self._prepare_trade_request(order)
            request["action"] = mt5.TRADE_ACTION_PENDING
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return TradeResponse(
                    order_id=0,
                    status="error",
                    message=f"Failed to place pending order: {result.comment}"
                )
            
            return TradeResponse(
                order_id=result.order,
                status="success",
                message="Pending order placed successfully"
            )
        except Exception as e:
            logger.error(f"Error placing pending order: {str(e)}")
            return TradeResponse(order_id=0, status="error", message=str(e))

    async def cancel_pending_order(self, ticket: int) -> TradeResponse:
        """
        Cancel an existing pending order.
        
        Parameters:
        - ticket: Pending order ticket to cancel
        
        Returns:
        - TradeResponse with:
            - order_id: Cancelled order ticket (0 if failed)
            - status: Success/error status
            - message: Cancellation details or error message
            
        Note: Returns error if order not found or already executed
        """
        if not await self.base_service.ensure_connected():
            return TradeResponse(order_id=0, status="error", message="Not connected to MT5")
        try:
            request = {
                "action": mt5.TRADE_ACTION_REMOVE,
                "order": ticket,
            }
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                return TradeResponse(
                    order_id=0,
                    status="error",
                    message=f"Failed to cancel order: {result.comment}"
                )
            return TradeResponse(
                order_id=ticket,
                status="success",
                message="Order cancelled successfully"
            )
        except Exception as e:
            logger.error(f"Error cancelling order: {str(e)}")
            return TradeResponse(order_id=0, status="error", message=str(e)) 