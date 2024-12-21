import MetaTrader5 as mt5
import logging
import asyncio
from typing import Optional

logger = logging.getLogger(__name__)

class MT5BaseService:
    _instance = None
    _initialized = False
    _login_info = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MT5BaseService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Skip initialization if already done
        if self._initialized:
            return
            
        self.reconnect_attempts = 3
        self.reconnect_delay = 5
        
    @property
    def initialized(self):
        return self._initialized

    @property
    def login_info(self):
        return self._login_info
        
    async def connect(self, login: int, password: str, server: str) -> bool:
        """Connect to MT5 terminal"""
        if not mt5.initialize():
            return False
            
        # Attempt to login
        if not mt5.login(login=login, password=password, server=server):
            mt5.shutdown()
            return False
            
        self._initialized = True
        return True

    async def ensure_connected(self) -> bool:
        """Ensure MT5 connection is active"""
        if not self._initialized:
            return False
        return mt5.terminal_info() is not None

    async def shutdown(self):
        """Shutdown MT5 connection"""
        if self._initialized:
            mt5.shutdown()
            self._initialized = False
            logger.info("MT5 connection closed")

    def __del__(self):
        """Cleanup when service is destroyed"""
        if self._initialized:
            mt5.shutdown() 