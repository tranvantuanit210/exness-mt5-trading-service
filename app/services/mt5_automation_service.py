import asyncio
import logging
from datetime import datetime, time
from decimal import Decimal
from typing import List, Dict, Optional, Union
import MetaTrader5 as mt5
from .mt5_base_service import MT5BaseService
from ..models.automation import (
    ScheduledTrade, ConditionalOrder, 
    GridTradingConfig, MartingaleConfig
)

logger = logging.getLogger(__name__)

class MT5AutomationService:
    def __init__(self, base_service: MT5BaseService):
        self.base_service = base_service
        self.scheduled_trades: List[ScheduledTrade] = []
        self.conditional_orders: List[ConditionalOrder] = []
        self.grid_configs: Dict[str, GridTradingConfig] = {}
        self.martingale_configs: Dict[str, MartingaleConfig] = {}
        self.running_tasks = []

    async def start_automation(self):
        """Start all automation tasks"""
        self.running_tasks.append(asyncio.create_task(self._schedule_monitor()))
        self.running_tasks.append(asyncio.create_task(self._condition_monitor()))
        self.running_tasks.append(asyncio.create_task(self._grid_monitor()))
        self.running_tasks.append(asyncio.create_task(self._martingale_monitor()))

    async def stop_automation(self):
        """Stop all automation tasks"""
        for task in self.running_tasks:
            task.cancel()
        self.running_tasks.clear()

    async def add_scheduled_trade(self, trade: ScheduledTrade) -> bool:
        """Add new scheduled trade"""
        self.scheduled_trades.append(trade)
        return True

    async def add_conditional_order(self, order: ConditionalOrder) -> bool:
        """Add new conditional order"""
        self.conditional_orders.append(order)
        return True

    async def setup_grid_trading(self, config: GridTradingConfig) -> bool:
        """Setup grid trading for symbol"""
        self.grid_configs[config.symbol] = config
        await self._initialize_grid(config)
        return True

    async def setup_martingale(self, config: MartingaleConfig) -> bool:
        """Setup martingale strategy"""
        self.martingale_configs[config.symbol] = config
        return True

    async def _schedule_monitor(self):
        """Monitor and execute scheduled trades"""
        while True:
            try:
                current_time = datetime.now().time()
                for trade in self.scheduled_trades[:]:
                    if self._should_execute_schedule(trade, current_time):
                        await self._execute_trade(trade)
                        if trade.schedule_type == "once":
                            self.scheduled_trades.remove(trade)
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Schedule monitor error: {str(e)}")
                await asyncio.sleep(5)

    async def _condition_monitor(self):
        """Monitor and execute conditional orders"""
        while True:
            try:
                for order in self.conditional_orders[:]:
                    if await self._check_conditions(order.conditions):
                        await self._execute_trade(order)
                        self.conditional_orders.remove(order)
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Condition monitor error: {str(e)}")
                await asyncio.sleep(5)

    async def _grid_monitor(self):
        """Monitor and manage grid trading"""
        while True:
            try:
                for symbol, config in self.grid_configs.items():
                    await self._manage_grid(config)
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Grid monitor error: {str(e)}")
                await asyncio.sleep(5)

    async def _martingale_monitor(self):
        """Monitor and manage martingale strategies"""
        while True:
            try:
                for symbol, config in self.martingale_configs.items():
                    await self._manage_martingale(config)
                await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Martingale monitor error: {str(e)}")
                await asyncio.sleep(5)

    def _should_execute_schedule(self, trade: ScheduledTrade, current_time: time) -> bool:
        """Check if scheduled trade should be executed"""
        if trade.expiry_date and datetime.now() > trade.expiry_date:
            return False
        return trade.execution_time <= current_time

    async def _check_conditions(self, conditions: List[Dict]) -> bool:
        """Check if all conditions are met"""
        for condition in conditions:
            if not await self._evaluate_condition(condition):
                return False
        return True

    async def _evaluate_condition(self, condition: Dict) -> bool:
        """Evaluate single trading condition"""
        condition_type = condition.get('type')
        symbol = condition.get('symbol')
        value = condition.get('value')

        if condition_type == 'price_above':
            current_price = await self.base_service.get_current_price(symbol)
            return current_price > Decimal(str(value))
        
        elif condition_type == 'price_below':
            current_price = await self.base_service.get_current_price(symbol)
            return current_price < Decimal(str(value))
        
        elif condition_type == 'ma_crossover':
            # Check MA crossover condition
            fast_ma = await self.base_service.get_ma(symbol, condition['fast_period'])
            slow_ma = await self.base_service.get_ma(symbol, condition['slow_period'])
            return fast_ma[-1] > slow_ma[-1] and fast_ma[-2] < slow_ma[-2]
        
        elif condition_type == 'rsi_above':
            rsi = await self.base_service.get_rsi(symbol, 14)
            return rsi[-1] > value
        
        elif condition_type == 'rsi_below':
            rsi = await self.base_service.get_rsi(symbol, 14)
            return rsi[-1] < value

        return False

    async def _execute_trade(self, trade: Union[ScheduledTrade, ConditionalOrder]) -> bool:
        """Execute trade with given parameters"""
        try:
            # Check risk management before execution
            if not await self.base_service.check_risk_limits(
                trade.symbol, 
                trade.volume,
                trade.order_type
            ):
                logger.warning(f"Risk limits exceeded for trade {trade}")
                return False

            # Execute order through base service
            result = await self.base_service.place_order(
                symbol=trade.symbol,
                order_type=trade.order_type,
                volume=trade.volume,
                price=trade.price,
                stop_loss=trade.stop_loss,
                take_profit=trade.take_profit
            )
            
            if result:
                logger.info(f"Successfully executed trade: {trade}")
                return True
            else:
                logger.error(f"Failed to execute trade: {trade}")
                return False

        except Exception as e:
            logger.error(f"Error executing trade: {str(e)}")
            return False

    async def _initialize_grid(self, config: GridTradingConfig):
        """Initialize grid trading levels"""
        try:
            current_price = await self.base_service.get_current_price(config.symbol)
            grid_size = config.grid_size
            price_distance = config.price_distance

            # Create buy orders grid below current price
            for i in range(1, grid_size + 1):
                buy_price = current_price - (price_distance * i)
                await self.base_service.place_order(
                    symbol=config.symbol,
                    order_type="BUY_LIMIT",
                    volume=config.volume_per_grid,
                    price=buy_price,
                    take_profit=buy_price + config.take_profit_distance
                )

            # Create sell orders grid above current price
            for i in range(1, grid_size + 1):
                sell_price = current_price + (price_distance * i)
                await self.base_service.place_order(
                    symbol=config.symbol,
                    order_type="SELL_LIMIT",
                    volume=config.volume_per_grid,
                    price=sell_price,
                    take_profit=sell_price - config.take_profit_distance
                )

        except Exception as e:
            logger.error(f"Error initializing grid: {str(e)}")

    async def _manage_grid(self, config: GridTradingConfig):
        """Manage existing grid positions"""
        try:
            # Get all open orders for symbol
            open_positions = await self.base_service.get_open_positions(config.symbol)
            pending_orders = await self.base_service.get_pending_orders(config.symbol)

            # Check and replace executed grid orders
            current_price = await self.base_service.get_current_price(config.symbol)
            
            # Calculate required grid orders on each side
            required_buys = sum(1 for order in pending_orders 
                              if order.type == "BUY_LIMIT")
            required_sells = sum(1 for order in pending_orders 
                               if order.type == "SELL_LIMIT")

            # Add new orders if needed
            if required_buys < config.grid_size:
                lowest_buy = min((order.price for order in pending_orders 
                                if order.type == "BUY_LIMIT"), default=current_price)
                new_buy_price = lowest_buy - config.price_distance
                
                await self.base_service.place_order(
                    symbol=config.symbol,
                    order_type="BUY_LIMIT",
                    volume=config.volume_per_grid,
                    price=new_buy_price,
                    take_profit=new_buy_price + config.take_profit_distance
                )

            if required_sells < config.grid_size:
                highest_sell = max((order.price for order in pending_orders 
                                  if order.type == "SELL_LIMIT"), default=current_price)
                new_sell_price = highest_sell + config.price_distance
                
                await self.base_service.place_order(
                    symbol=config.symbol,
                    order_type="SELL_LIMIT",
                    volume=config.volume_per_grid,
                    price=new_sell_price,
                    take_profit=new_sell_price - config.take_profit_distance
                )

        except Exception as e:
            logger.error(f"Error managing grid: {str(e)}")

    async def _manage_martingale(self, config: MartingaleConfig):
        """Manage martingale strategy"""
        try:
            # Get current position for symbol
            positions = await self.base_service.get_open_positions(config.symbol)
            
            if not positions:
                # If no position exists, place initial order
                if config.current_step == 0:
                    await self.base_service.place_order(
                        symbol=config.symbol,
                        order_type=config.initial_order_type,
                        volume=config.initial_volume,
                        stop_loss=config.stop_loss,
                        take_profit=config.take_profit
                    )
                    config.current_step += 1
            else:
                # Check if position is losing and needs martingale
                position = positions[0]  # Get first position
                
                if position.profit < 0 and config.current_step < config.max_steps:
                    # Calculate new volume based on martingale multiplier
                    new_volume = position.volume * config.multiplier
                    
                    # Close old position
                    await self.base_service.close_position(position.ticket)
                    
                    # Open new position with larger volume
                    await self.base_service.place_order(
                        symbol=config.symbol,
                        order_type=position.type,
                        volume=new_volume,
                        stop_loss=config.stop_loss,
                        take_profit=config.take_profit
                    )
                    
                    config.current_step += 1
                
                elif position.profit > 0:
                    # Reset martingale if profitable
                    config.current_step = 0

        except Exception as e:
            logger.error(f"Error managing martingale: {str(e)}") 