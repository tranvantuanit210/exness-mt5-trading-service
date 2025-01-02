import logging
from typing import List, Optional
from datetime import datetime, timedelta

import motor.motor_asyncio
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from ..models.signal import TradingSignal
from .mt5_base_service import MT5BaseService
from ..config import settings
from ..utils.exceptions import DatabaseConnectionError, SignalNotFoundError

logger = logging.getLogger(__name__)

# Constants
DEFAULT_LIMIT = 100

class MT5SignalService:
    """Service for managing trading signals in MongoDB."""
    
    def __init__(self, base_service: MT5BaseService):
        """
        Initialize signal service.
        
        Args:
            base_service: Base MT5 service instance
            
        Raises:
            DatabaseConnectionError: If MongoDB connection fails
        """
        self.base = base_service
        try:
            self.client: AsyncIOMotorClient = motor.motor_asyncio.AsyncIOMotorClient(
                settings.MONGODB_URL
            )
            self.db: AsyncIOMotorDatabase = self.client[settings.MONGODB_DB]
            self.signals = self.db.signals
            logger.info("MongoDB connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise DatabaseConnectionError("Could not connect to MongoDB") from e

    async def add_signal(self, signal: TradingSignal) -> dict:
        """
        Add new trading signal to database.
        
        Args:
            signal: Trading signal to add
            
        Returns:
            dict: Result with signal ID and status
            
        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            result = await self.signals.insert_one(signal.dict())
            signal_id = str(result.inserted_id)
            logger.info(f"Added new signal with ID: {signal_id}")
            return {"id": signal_id, "status": "success"}
        except Exception as e:
            logger.error(f"Failed to add signal: {str(e)}")
            raise DatabaseConnectionError("Could not add signal to database") from e

    async def get_signals(
        self,
        symbol: Optional[str] = None,
        timeframe: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = DEFAULT_LIMIT
    ) -> List[TradingSignal]:
        """
        Get trading signals with optional filters.
        
        Args:
            symbol: Filter by trading symbol
            timeframe: Filter by timeframe
            start_date: Filter by start date
            end_date: Filter by end date
            limit: Maximum number of signals to return
            
        Returns:
            List[TradingSignal]: List of trading signals
            
        Raises:
            DatabaseConnectionError: If database operation fails
        """
        try:
            query = {}
            if symbol:
                query["symbol"] = symbol
            if timeframe:
                query["timeframe"] = timeframe
            if start_date:
                query["created_at"] = {"$gte": start_date}
            if end_date:
                query.setdefault("created_at", {}).update({"$lte": end_date})

            cursor = self.signals.find(query).sort("created_at", -1).limit(limit)
            signals = []
            async for signal in cursor:
                signal["_id"] = str(signal["_id"])
                signals.append(TradingSignal(**signal))
                
            logger.info(f"Retrieved {len(signals)} signals")
            return signals
            
        except Exception as e:
            logger.error(f"Failed to get signals: {str(e)}")
            raise DatabaseConnectionError("Could not retrieve signals from database") from e

    async def delete_signal(self, signal_id: str) -> dict:
        """
        Delete trading signal by ID.
        
        Args:
            signal_id: ID of signal to delete
            
        Returns:
            dict: Operation result status and message
            
        Raises:
            SignalNotFoundError: If signal not found
            DatabaseConnectionError: If database operation fails
        """
        try:
            result = await self.signals.delete_one({"_id": ObjectId(signal_id)})
            if result.deleted_count:
                logger.info(f"Deleted signal with ID: {signal_id}")
                return {"status": "success", "message": "Signal deleted"}
            
            logger.warning(f"Signal not found with ID: {signal_id}")
            raise SignalNotFoundError(f"Signal with ID {signal_id} not found")
            
        except Exception as e:
            logger.error(f"Failed to delete signal: {str(e)}")
            raise DatabaseConnectionError("Could not delete signal from database") from e

    async def cleanup(self):
        """Close MongoDB connection."""
        if hasattr(self, 'client'):
            self.client.close()
            logger.info("MongoDB connection closed") 

    async def get_signals_by_symbol(
        self,
        symbol: str,
        timeframes: List[str],
        from_date: datetime,
        to_date: datetime
    ) -> List[TradingSignal]:
        """
        Get signals for a symbol with multiple timeframes within a date range
        
        Args:
            symbol: Trading symbol to get signals for
            timeframes: List of timeframes to include
            from_date: Start date time
            to_date: End date time
            
        Returns:
            List of TradingSignal objects matching the criteria
        """
        try:
            signals = await self.signals.find({
                "symbol": symbol,
                "timeframe": {"$in": timeframes},
                "created_at": {
                    "$gte": from_date,
                    "$lte": to_date
                }
            }).sort("created_at", -1).to_list(None)
            
            return [TradingSignal(**signal) for signal in signals]
        except Exception as e:
            logger.error(f"Error getting signals for symbol {symbol}: {str(e)}")
            raise 