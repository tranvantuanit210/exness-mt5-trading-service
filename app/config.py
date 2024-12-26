from pydantic_settings import BaseSettings
from typing import Optional, List

class Settings(BaseSettings):
    # MT5 Settings
    MT5_LOGIN: int
    MT5_PASSWORD: str
    MT5_SERVER: str
    
    # Notification Settings
    TELEGRAM_BOT_TOKEN: str
    TELEGRAM_CHAT_ID: str
    DISCORD_WEBHOOK_URL: str
    
    # MongoDB settings
    MONGODB_URL: str
    MONGODB_DB: str

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings() 