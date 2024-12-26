class DatabaseConnectionError(Exception):
    """Raised when database connection fails"""
    pass

class SignalNotFoundError(Exception):
    """Raised when signal is not found in database"""
    pass

class ValidationError(Exception):
    """Raised when data validation fails"""
    pass

class ServiceError(Exception):
    """Base class for service-related errors"""
    pass

class MT5ConnectionError(ServiceError):
    """Raised when MT5 connection fails"""
    pass

class TradeExecutionError(ServiceError):
    """Raised when trade execution fails"""
    pass 