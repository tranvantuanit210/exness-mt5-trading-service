from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # MT5 Settings
    MT5_LOGIN: int
    MT5_PASSWORD: str
    MT5_SERVER: str
    
    # Notification Settings
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None
    DISCORD_WEBHOOK_URL: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 