import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from .mt5_base_service import MT5BaseService
from ..models.reporting import TradeStats, PairAnalysis, DrawdownInfo, PeriodicReport

logger = logging.getLogger(__name__)

class MT5ReportingService:
    def __init__(self, base_service: MT5BaseService):
        self.base_service = base_service

    async def get_performance_stats(self, start_date: datetime, end_date: datetime, period: str) -> TradeStats:
        """Calculate trading performance statistics"""
        try:
            trades = await self.base_service.get_trades_history(start_date, end_date)
            
            total_trades = len(trades)
            winning_trades = sum(1 for trade in trades if trade.profit > 0)
            
            win_rate = winning_trades / total_trades if total_trades > 0 else 0
            avg_profit = sum(trade.profit for trade in trades) / total_trades if total_trades > 0 else 0
            
            initial_balance = await self.base_service.get_balance_history(start_date)
            final_balance = await self.base_service.get_balance_history(end_date)
            roi = (final_balance - initial_balance) / initial_balance if initial_balance > 0 else 0

            return TradeStats(
                total_trades=total_trades,
                winning_trades=winning_trades,
                losing_trades=total_trades - winning_trades,
                win_rate=win_rate,
                avg_profit=avg_profit,
                roi=roi,
                period=period,
                start_date=start_date,
                end_date=end_date
            )
        except Exception as e:
            logger.error(f"Error calculating performance stats: {str(e)}")
            raise

    async def analyze_pair(self, symbol: str, period: int = 30) -> PairAnalysis:
        """Analyze trading performance for specific symbol"""
        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days=period)
            
            trades = await self.base_service.get_symbol_trades(symbol, start_date, end_date)
            
            total_profit = sum(trade.profit for trade in trades)
            win_rate = sum(1 for trade in trades if trade.profit > 0) / len(trades) if trades else 0
            
            # Calculate average spread
            spreads = await self.base_service.get_symbol_spreads(symbol, period=24)
            avg_spread = sum(spreads) / len(spreads) if spreads else 0
            
            # Analyze best trading hours
            hour_profits = {}
            for trade in trades:
                hour = trade.open_time.hour
                hour_profits[hour] = hour_profits.get(hour, 0) + trade.profit
            
            best_hours = sorted(hour_profits.keys(), 
                              key=lambda x: hour_profits[x], 
                              reverse=True)[:3]

            # Calculate risk score based on volatility and drawdown
            volatility = await self.base_service.get_symbol_volatility(symbol)
            risk_score = volatility * (1 - win_rate)  # Simple risk calculation

            return PairAnalysis(
                symbol=symbol,
                total_profit=total_profit,
                total_trades=len(trades),
                win_rate=win_rate,
                avg_spread=avg_spread,
                best_trading_hours=best_hours,
                risk_score=risk_score
            )
        except Exception as e:
            logger.error(f"Error analyzing pair {symbol}: {str(e)}")
            raise

    async def monitor_drawdown(self) -> DrawdownInfo:
        """Monitor and analyze drawdown"""
        try:
            balance_history = await self.base_service.get_balance_history()
            
            # Calculate current drawdown
            peak_balance = max(balance_history)
            current_balance = balance_history[-1]
            current_drawdown = (peak_balance - current_balance) / peak_balance
            
            # Calculate maximum drawdown
            max_drawdown = 0
            drawdown_periods = []
            current_peak = balance_history[0]
            drawdown_start = None
            
            for date, balance in balance_history:
                if balance > current_peak:
                    current_peak = balance
                    drawdown_start = None
                else:
                    drawdown = (current_peak - balance) / current_peak
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown
                    
                    if drawdown > 0.05 and drawdown_start is None:  # 5% threshold
                        drawdown_start = date
                    elif drawdown < 0.05 and drawdown_start is not None:
                        drawdown_periods.append({
                            'start': drawdown_start,
                            'end': date
                        })
                        drawdown_start = None

            # Determine risk level
            risk_level = 'LOW' if max_drawdown < 0.1 else 'MEDIUM' if max_drawdown < 0.2 else 'HIGH'

            return DrawdownInfo(
                current_drawdown=current_drawdown,
                max_drawdown=max_drawdown,
                drawdown_periods=drawdown_periods,
                recovery_time=None,  # Calculate if needed
                risk_level=risk_level
            )
        except Exception as e:
            logger.error(f"Error monitoring drawdown: {str(e)}")
            raise

    async def generate_periodic_report(self, period: str) -> PeriodicReport:
        """Generate periodic report"""
        try:
            end_date = datetime.now()
            if period == 'daily':
                start_date = end_date - timedelta(days=1)
            elif period == 'weekly':
                start_date = end_date - timedelta(weeks=1)
            elif period == 'monthly':
                start_date = end_date - timedelta(days=30)
            else:
                raise ValueError(f"Invalid period: {period}")

            # Get account statistics
            account_info = await self.base_service.get_account_info()
            trades = await self.base_service.get_trades_history(start_date, end_date)
            
            # Get top performing pairs
            symbols = await self.base_service.get_traded_symbols()
            pair_analyses = []
            for symbol in symbols:
                analysis = await self.analyze_pair(symbol)
                pair_analyses.append(analysis)
            
            top_pairs = sorted(pair_analyses, 
                             key=lambda x: x.total_profit, 
                             reverse=True)[:5]

            # Get drawdown information
            drawdown_info = await self.monitor_drawdown()

            return PeriodicReport(
                period=period,
                start_date=start_date,
                end_date=end_date,
                account_balance=account_info.balance,
                net_profit=sum(trade.profit for trade in trades),
                total_trades=len(trades),
                win_rate=sum(1 for trade in trades if trade.profit > 0) / len(trades) if trades else 0,
                top_pairs=top_pairs,
                drawdown_info=drawdown_info
            )
        except Exception as e:
            logger.error(f"Error generating periodic report: {str(e)}")
            raise 