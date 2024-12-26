from typing import Dict, Any
import MetaTrader5 as mt5
import logging
from .mt5_base_service import MT5BaseService
from ..models.trade import (
    TradeRequest, TradeResponse, OrderType
)
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio
from ..utils.retry_helper import handle_retry_error
from ..utils.constants import (
    MAX_RETRIES, VERIFICATION_WAIT_TIME, 
    TRADE_DEVIATION, TRADE_MAGIC,
    RETRY_MULTIPLIER, RETRY_MIN_WAIT, RETRY_MAX_WAIT
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
        self.max_retries = MAX_RETRIES

    @property
    def initialized(self):
        """Check if trading service is initialized and connected"""
        return self.base_service.initialized

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=RETRY_MULTIPLIER, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
        retry_error_callback=lambda retry_state: handle_retry_error(retry_state, max_retries=MAX_RETRIES)
    )
    async def execute_market_order(self, trade_request: TradeRequest) -> TradeResponse:
        """
        Execute a market order with specified investment amount
        
        Args:
            trade_request: Trading request containing symbol, order type, amount and optional SL/TP
            
        Returns:
            TradeResponse: Order execution result with status and details
        """
        if not await self.base_service.ensure_connected():
            return TradeResponse(
                order_id=0,
                status="error",
                message="Failed to connect to MT5"
            )

        try:
            # Calculate volume from investment amount
            volume = await self.calculate_volume_from_amount(
                trade_request.symbol, 
                trade_request.amount
            )
            
            # Add volume to trade_request for verification
            trade_request.calculated_volume = volume
            
            # Prepare trade request with calculated volume
            tick = mt5.symbol_info_tick(trade_request.symbol)
            if tick is None:
                raise ValueError(f"Cannot get symbol info for {trade_request.symbol}")
                
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": trade_request.symbol,
                "volume": float(volume),  # Use calculated volume
                "type": (mt5.ORDER_TYPE_BUY 
                        if trade_request.order_type == OrderType.BUY 
                        else mt5.ORDER_TYPE_SELL),
                "price": tick.ask if trade_request.order_type == OrderType.BUY else tick.bid,
                "deviation": TRADE_DEVIATION,
                "magic": TRADE_MAGIC,
                "comment": trade_request.comment or "python market order",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            if trade_request.stop_loss:
                request["sl"] = float(trade_request.stop_loss)
            if trade_request.take_profit:
                request["tp"] = float(trade_request.take_profit)

            # Execute the trade
            result = mt5.order_send(request)
            
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                logger.error(f"Order failed: {result.comment}")
                return TradeResponse(
                    order_id=0,
                    status="error",
                    message=f"Order failed: {result.comment}"
                )

            # Verify trade result with the calculated volume
            verified = await self._verify_trade_result(result, trade_request)
            if not verified:
                logger.error("Trade verification failed")
                return TradeResponse(
                    order_id=0, 
                    status="error",
                    message="Trade verification failed"
                )

            logger.info(f"Order placed and verified successfully: Order ID {result.order}")
            return TradeResponse(
                order_id=result.order,
                symbol=trade_request.symbol,
                status="success",
                message="Order placed and verified successfully"
            )

        except Exception as e:
            logger.error(f"Error placing order: {str(e)}")
            return TradeResponse(
                order_id=0,
                status="error",
                message=str(e)
            )

    async def _verify_trade_result(self, result: mt5.OrderSendResult, original_request: TradeRequest) -> bool:
        """
        Verify trade execution by comparing position details with original request
        """
        try:
            await asyncio.sleep(VERIFICATION_WAIT_TIME)
            
            position = mt5.positions_get(ticket=result.order)
            if not position:
                logger.error(f"Cannot find position with ticket {result.order}")
                return False
                
            position = position[0]
            
            # Verify critical parameters using calculated_volume
            if (position.symbol != original_request.symbol or
                position.volume != float(original_request.calculated_volume) or
                (position.type == mt5.ORDER_TYPE_BUY and original_request.order_type != OrderType.BUY) or
                (position.type == mt5.ORDER_TYPE_SELL and original_request.order_type != OrderType.SELL)):
                logger.error("Trade parameters mismatch")
                return False
                
            # Verify SL/TP if specified
            if original_request.stop_loss and position.sl != float(original_request.stop_loss):
                logger.error("Stop Loss mismatch")
                return False
                
            if original_request.take_profit and position.tp != float(original_request.take_profit):
                logger.error("Take Profit mismatch")
                return False

            return True

        except Exception as e:
            logger.error(f"Error during trade verification: {str(e)}")
            return False 

    async def calculate_min_amount(self, symbol: str) -> float:
        """
        Calculate minimum required amount in USD for trading
        
        Args:
            symbol: Trading symbol (e.g., BTCUSDm)
            
        Returns:
            float: Minimum amount required in USD
            
        Raises:
            ValueError: If symbol not found
        """
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            raise ValueError(f"Symbol {symbol} not found")
            
        min_volume = symbol_info.volume_min
        contract_size = symbol_info.trade_contract_size
        current_price = symbol_info.ask
        
        min_amount = min_volume * contract_size * current_price
        return round(min_amount, 2)

    async def calculate_volume_from_amount(self, symbol: str, amount: float) -> float:
        """
        Calculate trading volume (lot size) based on investment amount
        
        Args:
            symbol: Trading symbol (e.g., BTCUSDm)
            amount: Investment amount in deposit currency
            
        Returns:
            float: Calculated trading volume in lots
            
        Raises:
            ValueError: If symbol not found or amount is outside allowed limits
        """
        symbol_info = mt5.symbol_info(symbol)
        if symbol_info is None:
            raise ValueError(f"Symbol {symbol} not found")
            
        current_price = symbol_info.ask
        contract_size = symbol_info.trade_contract_size
        
        volume = round(amount / (contract_size * current_price), 2)
        
        min_volume = symbol_info.volume_min
        max_volume = symbol_info.volume_max
        
        if volume < min_volume:
            min_amount = await self.calculate_min_amount(symbol)
            raise ValueError(
                f"Amount too small. Minimum required amount: ${min_amount} USD "
                f"(minimum volume: {min_volume} lots)"
            )
        if volume > max_volume:
            max_amount = max_volume * contract_size * current_price
            raise ValueError(
                f"Amount too large. Maximum allowed amount: ${round(max_amount, 2)} USD "
                f"(maximum volume: {max_volume} lots)"
            )
            
        return volume
 