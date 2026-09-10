import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "AI News Intelligence Platform"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "127.0.0.1"

    # 'live' (uses live APIs/RSS) or 'demo' (100% offline sample news)
    APP_MODE: str = "demo"

    # SQLite Database File Path
    DATABASE_URL: str = "sqlite:///./data/news_intelligence.db"

    # External APIs (Optional)
    NEWS_API_KEY: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
