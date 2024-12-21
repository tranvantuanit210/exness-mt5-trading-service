from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv
import logging
import uvicorn
from contextlib import asynccontextmanager
from typing import List, Optional

from app.models.trade import TradeRequest, TradeResponse, Position, AccountInfo
from app.services.mt5_service import MT5Service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Create MT5 service instance
mt5_service = MT5Service()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan event handler for FastAPI application
    Handles startup and shutdown events
    """
    # Startup: Connect to MT5
    try:
        connected = await mt5_service.connect(
            login=int(os.getenv("MT5_LOGIN")),
            password=os.getenv("MT5_PASSWORD"),
            server=os.getenv("MT5_SERVER")
        )
        if not connected:
            raise Exception("Failed to connect to MT5")
    except Exception as e:
        logger.error(f"Startup error: {str(e)}")
        raise
    
    yield  # Application running
    
    # Shutdown: Cleanup MT5 connection
    if mt5_service.initialized:
        logger.info("Shutting down MT5 connection")
        await mt5_service.shutdown()

# Initialize FastAPI with lifespan
app = FastAPI(
    title="MT5 Trading API",
    description="API for automated trading through MetaTrader 5",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/trade", 
         response_model=TradeResponse,
         summary="Execute trade",
         description="Place a new trading order in MT5")
async def execute_trade(trade_request: TradeRequest):
    """
    Execute a trading order:
    - Validate input data
    - Send order to MT5
    - Return execution result
    """
    try:
        result = await mt5_service.place_order(trade_request)
        if result.status == "error":
            raise HTTPException(status_code=400, detail=result.message)
        return result
    except Exception as e:
        logger.error(f"Trade error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health",
         summary="Check status",
         description="Check MT5 connection status")
async def health_check():
    """Check connection status endpoint"""
    return {
        "status": "healthy" if mt5_service.initialized else "unhealthy",
        "message": "Connected to MT5" if mt5_service.initialized else "Not connected to MT5"
    }

@app.get("/positions",
         response_model=List[Position],
         summary="Get open positions",
         description="Get all open positions from MT5")
async def get_positions():
    """Get all open positions"""
    return await mt5_service.get_positions()

@app.get("/account",
         response_model=Optional[AccountInfo],
         summary="Get account info",
         description="Get MT5 account information")
async def get_account_info():
    """Get account information"""
    info = await mt5_service.get_account_info()
    if info is None:
        raise HTTPException(status_code=500, detail="Failed to get account info")
    return info

@app.delete("/positions/{ticket}",
            response_model=TradeResponse,
            summary="Close position",
            description="Close specific position by ticket")
async def close_position(ticket: int):
    """Close position by ticket"""
    result = await mt5_service.close_position(ticket)
    if result.status == "error":
        raise HTTPException(status_code=400, detail=result.message)
    return result

def main():
    """
    Main entry point for debugging
    """
    # You can add initialization code here
    logger.info("Starting MT5 Trading API")
    
    # Run the FastAPI application
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="debug"
    )

if __name__ == "__main__":
    main() 