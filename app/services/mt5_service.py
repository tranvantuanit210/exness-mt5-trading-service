from typing import Optional, Dict, Any
import MetaTrader5 as mt5
import logging
from ..models.trade import TradeRequest, TradeResponse, OrderType, Position, AccountInfo
from decimal import Decimal
import asyncio
from datetime import datetime
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class MT5Service:
    def __init__(self):
        self.initialized = False
        self.login_info = None
        self.reconnect_attempts = 3
        self.reconnect_delay = 5
        
    async def connect(self, login: int, password: str, server: str) -> bool:
        """
        Connect to MT5 terminal
        
        Args:
            login: MT5 account login
            password: MT5 account password
            server: MT5 server name
            
        Returns:
            bool: True if connection successful, False otherwise
        """
        self.login_info = {
            "login": login,
            "password": password,
            "server": server
        }
        
        return await self._connect()
    
    async def _connect(self) -> bool:
        """Internal connection method with retry logic"""
        if not self.login_info:
            logger.error("No login information available")
            return False
            
        for attempt in range(self.reconnect_attempts):
            try:
                if self.initialized:
                    return True
                
                if not mt5.initialize():
                    logger.error("MT5 initialization failed")
                    if attempt < self.reconnect_attempts - 1:
                        await asyncio.sleep(self.reconnect_delay)
                        continue
                    return False
                
                login_result = mt5.login(
                    login=self.login_info["login"],
                    password=self.login_info["password"],
                    server=self.login_info["server"]
                )
                
                if login_result:
                    self.initialized = True
                    logger.info(f"Connected to MT5 server: {self.login_info['server']}")
                    return True
                    
                logger.error(f"MT5 login failed, attempt {attempt + 1}/{self.reconnect_attempts}")
                
                if attempt < self.reconnect_attempts - 1:
                    await asyncio.sleep(self.reconnect_delay)
                    
            except Exception as e:
                logger.error(f"MT5 connection error: {str(e)}")
                if attempt < self.reconnect_attempts - 1:
                    await asyncio.sleep(self.reconnect_delay)
                    
        return False

    async def ensure_connected(self) -> bool:
        """Ensure MT5 connection is active, reconnect if necessary"""
        if not self.initialized:
            logger.info("MT5 not initialized, attempting to reconnect")
            return await self._connect()
        return True

    def _prepare_trade_request(self, trade_request: TradeRequest) -> Dict[str, Any]:
        """Prepare trade request parameters for MT5"""
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

    async def place_order(self, trade_request: TradeRequest) -> TradeResponse:
        """Place a trading order in MT5"""
        if not await self.ensure_connected():
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
            self.initialized = False
            return TradeResponse(
                order_id=0,
                status="error",
                message=str(e)
            )

    async def shutdown(self):
        """Shutdown MT5 connection"""
        if self.initialized:
            mt5.shutdown()
            self.initialized = False
            logger.info("MT5 connection closed")

    def __del__(self):
        """Cleanup when service is destroyed"""
        if self.initialized:
            mt5.shutdown()

    async def get_positions(self) -> List[Position]:
        """Get all open positions"""
        if not await self.ensure_connected():
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

    async def get_account_info(self) -> Optional[AccountInfo]:
        """Get account information"""
        if not await self.ensure_connected():
            return None
            
        try:
            account_info = mt5.account_info()
            if account_info is None:
                return None
                
            return AccountInfo(
                balance=Decimal(str(account_info.balance)),
                equity=Decimal(str(account_info.equity)),
                margin=Decimal(str(account_info.margin)),
                free_margin=Decimal(str(account_info.margin_free)),
                positions_count=account_info.open_positions
            )
            
        except Exception as e:
            logger.error(f"Error getting account info: {str(e)}")
            return None

    async def close_position(self, ticket: int) -> TradeResponse:
        """Close specific position by ticket"""
        if not await self.ensure_connected():
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