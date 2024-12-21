import logging
from ..models.trade import TradeResponse

logger = logging.getLogger(__name__)

def handle_retry_error(retry_state, max_retries: int = 3) -> TradeResponse:
    """
    Common handler for retry errors
    
    Args:
        retry_state: Current retry state containing error info
        max_retries: Maximum number of retries attempted
        
    Returns:
        TradeResponse with error details
    """
    logger.error(f"Max retries reached. Last error: {retry_state.outcome.exception()}")
    return TradeResponse(
        order_id=0,
        status="error",
        message=f"Failed after {max_retries} retries: {str(retry_state.outcome.exception())}"
    ) 