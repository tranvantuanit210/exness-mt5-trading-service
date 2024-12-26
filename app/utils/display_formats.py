from ..models.signal import TimeFrame

# Convert timeframe to human readable format
timeframe_display = {
    TimeFrame.M1: "1 minute",
    TimeFrame.M5: "5 minutes", 
    TimeFrame.M15: "15 minutes",
    TimeFrame.M30: "30 minutes",
    TimeFrame.H1: "1 hour",
    TimeFrame.H4: "4 hours",
    TimeFrame.D1: "1 day",
    TimeFrame.W1: "1 week",
    TimeFrame.MN1: "1 month"
}

def get_timeframe_display(timeframe: TimeFrame) -> str:
    """Convert TimeFrame enum to human readable string"""
    return timeframe_display.get(timeframe, str(timeframe)) 