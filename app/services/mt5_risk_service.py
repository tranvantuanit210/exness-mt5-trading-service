from decimal import Decimal
import pandas as pd
import MetaTrader5 as mt5
import logging
from typing import List, Dict, Optional
from .mt5_base_service import MT5BaseService
from ..models.risk_management import (
    PositionSizeRequest, PositionSizeResponse,
    TrailingStopRequest, PortfolioRiskRequest, PortfolioRiskResponse
)

logger = logging.getLogger(__name__)

class MT5RiskService:
    def __init__(self, base_service: MT5BaseService):
        self.base_service = base_service

    async def calculate_position_size(self, request: PositionSizeRequest) -> PositionSizeResponse:
        """Calculate optimal position size based on risk parameters"""
        if not await self.base_service.ensure_connected():
            raise Exception("Not connected to MT5")
            
        try:
            # Get account info
            account_info = mt5.account_info()
            if not account_info:
                raise Exception("Cannot get account info")
                
            # Get symbol info
            symbol_info = mt5.symbol_info(request.symbol)
            if not symbol_info:
                raise Exception(f"Cannot get symbol info for {request.symbol}")
                
            # Calculate risk amount
            balance = Decimal(str(account_info.balance))
            risk_amount = balance * request.risk_percent / Decimal('100')
            
            # Calculate stop loss in pips
            pip_size = Decimal('0.0001') if symbol_info.digits == 4 else Decimal('0.00001')
            stop_loss_pips = abs(request.entry_price - request.stop_loss) / pip_size
            
            # Calculate pip value
            contract_size = Decimal(str(symbol_info.trade_contract_size))
            pip_value = (pip_size * contract_size)
            
            # Calculate position size
            position_size = (risk_amount / (stop_loss_pips * pip_value)).quantize(Decimal('0.01'))
            
            # Ensure within symbol limits
            min_lot = Decimal(str(symbol_info.volume_min))
            max_lot = Decimal(str(symbol_info.volume_max))
            position_size = max(min(position_size, max_lot), min_lot)
            
            return PositionSizeResponse(
                position_size=position_size,
                risk_amount=risk_amount,
                pip_value=pip_value,
                stop_loss_pips=int(stop_loss_pips)
            )
            
        except Exception as e:
            logger.error(f"Error calculating position size: {str(e)}")
            raise

    async def manage_trailing_stop(self, request: TrailingStopRequest) -> bool:
        """Manage trailing stop loss for a position"""
        if not await self.base_service.ensure_connected():
            return False
            
        try:
            position = mt5.positions_get(ticket=request.ticket)
            if not position:
                return False
                
            position = position[0]
            current_price = mt5.symbol_info_tick(position.symbol).bid if position.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(position.symbol).ask
            
            # Calculate new stop loss level
            if position.type == mt5.ORDER_TYPE_BUY:
                new_sl = current_price - (request.trail_points * mt5.symbol_info(position.symbol).point)
                if not position.sl or new_sl > position.sl:
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": position.ticket,
                        "symbol": position.symbol,
                        "sl": new_sl,
                        "tp": position.tp
                    }
                    result = mt5.order_send(request)
                    return result.retcode == mt5.TRADE_RETCODE_DONE
            else:
                new_sl = current_price + (request.trail_points * mt5.symbol_info(position.symbol).point)
                if not position.sl or new_sl < position.sl:
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": position.ticket,
                        "symbol": position.symbol,
                        "sl": new_sl,
                        "tp": position.tp
                    }
                    result = mt5.order_send(request)
                    return result.retcode == mt5.TRADE_RETCODE_DONE
                    
            return True
            
        except Exception as e:
            logger.error(f"Error managing trailing stop: {str(e)}")
            return False

    async def analyze_portfolio_risk(self, request: PortfolioRiskRequest) -> PortfolioRiskResponse:
        """Analyze total portfolio risk and correlations"""
        if not await self.base_service.ensure_connected():
            raise Exception("Not connected to MT5")
            
        try:
            positions = mt5.positions_get()
            if not positions:
                return PortfolioRiskResponse(
                    total_risk_percent=Decimal('0'),
                    position_risks=[],
                    correlated_pairs=[],
                    risk_status="OK"
                )
                
            # Calculate individual position risks
            account_info = mt5.account_info()
            balance = Decimal(str(account_info.balance))
            position_risks = []
            total_risk = Decimal('0')
            
            for pos in positions:
                risk_amount = abs(pos.price_open - pos.sl) * pos.volume * mt5.symbol_info(pos.symbol).trade_contract_size if pos.sl else 0
                risk_percent = (Decimal(str(risk_amount)) / balance) * Decimal('100')
                total_risk += risk_percent
                
                position_risks.append({
                    "ticket": pos.ticket,
                    "symbol": pos.symbol,
                    "risk_percent": risk_percent,
                    "risk_amount": Decimal(str(risk_amount))
                })
                
            # Calculate correlations if multiple positions
            correlated_pairs = []
            if len(positions) > 1:
                symbols = [pos.symbol for pos in positions]
                rates_data = {}
                
                # Get historical data for correlation
                for symbol in symbols:
                    rates = mt5.copy_rates_from_pos(symbol, mt5.TIMEFRAME_H1, 0, 100)
                    if rates is not None:
                        rates_data[symbol] = pd.DataFrame(rates)['close']
                
                # Calculate correlation matrix
                if rates_data:
                    df = pd.DataFrame(rates_data)
                    corr_matrix = df.corr()
                    
                    # Find highly correlated pairs
                    for i in range(len(symbols)):
                        for j in range(i+1, len(symbols)):
                            correlation = abs(corr_matrix.iloc[i,j])
                            if correlation > request.correlation_threshold:
                                correlated_pairs.append({
                                    "symbol1": symbols[i],
                                    "symbol2": symbols[j],
                                    "correlation": Decimal(str(correlation))
                                })
            
            # Determine risk status
            risk_status = "OK"
            if total_risk > request.max_total_risk:
                risk_status = "DANGER"
            elif total_risk > request.max_total_risk * Decimal('0.8'):
                risk_status = "WARNING"
                
            return PortfolioRiskResponse(
                total_risk_percent=total_risk,
                position_risks=position_risks,
                correlated_pairs=correlated_pairs,
                risk_status=risk_status
            )
            
        except Exception as e:
            logger.error(f"Error analyzing portfolio risk: {str(e)}")
            raise 