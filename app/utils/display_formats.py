from ..models.signal import TimeFrame

# Convert timeframe to human readable format
timeframe_display = {
    TimeFrame.S1: "1 second",
    TimeFrame.S5: "5 seconds",
    TimeFrame.S15: "15 seconds",
    TimeFrame.S30: "30 seconds",
    TimeFrame.M1: "1 minute",
    TimeFrame.M3: "3 minutes",
    TimeFrame.M5: "5 minutes",
    TimeFrame.M15: "15 minutes",
    TimeFrame.M30: "30 minutes",
    TimeFrame.M45: "45 minutes",
    TimeFrame.H1: "1 hour",
    TimeFrame.H2: "2 hours",
    TimeFrame.H3: "3 hours",
    TimeFrame.H4: "4 hours",
    TimeFrame.D1: "1 day",
    TimeFrame.D5: "5 days",
    TimeFrame.W1: "1 week",
    TimeFrame.MN1: "1 month",
    TimeFrame.Q1: "1 quarter",
    TimeFrame.Y1: "1 year"
}

def get_timeframe_display(timeframe: TimeFrame) -> str:
    """Convert TimeFrame enum to human readable string"""
    return timeframe_display.get(timeframe, str(timeframe)) 