import MetaTrader5 as mt5
import logging

logger = logging.getLogger(__name__)

class MT5BaseService:
    """
    Base service for MT5 connection management.
    Handles initialization, connection, and cleanup of MT5 terminal connection.
    
    Implements singleton pattern to ensure only one connection instance exists.
    """
    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MT5BaseService, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """
        Initialize base service with reconnection settings.
        Skips if already initialized (singleton pattern).
        """
        if self._initialized:
            return
            
        self.reconnect_attempts = 3
        self.reconnect_delay = 5
        
    @property
    def initialized(self):
        """Check if MT5 connection is initialized"""
        return self._initialized
        
    async def connect(self, login: int, password: str, server: str) -> bool:
        """
        Connect to MT5 terminal with credentials.
        
        Parameters:
        - login: MT5 account number
        - password: MT5 account password
        - server: MT5 server name
        
        Returns:
        - bool: True if connection successful, False otherwise
        """
        if not mt5.initialize():
            return False
            
        if not mt5.login(login=login, password=password, server=server):
            mt5.shutdown()
            return False
            
        self._initialized = True
        return True

    async def ensure_connected(self) -> bool:
        """
        Verify MT5 connection is active.
        
        Returns:
        - bool: True if connected, False otherwise
        """
        if not self._initialized:
            return False
        return mt5.terminal_info() is not None

    async def shutdown(self):
        """
        Shutdown MT5 connection and cleanup resources.
        Logs connection closure for monitoring.
        """
        if self._initialized:
            mt5.shutdown()
            self._initialized = False
            logger.info("MT5 connection closed")

    def __del__(self):
        """
        Cleanup method called when service is destroyed.
        Ensures MT5 connection is properly closed.
        """
        if self._initialized:
            mt5.shutdown() 