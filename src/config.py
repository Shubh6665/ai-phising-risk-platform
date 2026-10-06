from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application configuration.
    Reads from environment variables and the local .env file.
    Pydantic automatically validates the types.
    """
    
    APP_ENV: str = "dev"
    
    # LLM Provider Configuration
    # We use a single string to determine which provider to use at runtime
    LLM_PROVIDER: str = "google"
    LLM_MODEL: str = "gemini-3.8-flash"
    
    # Provider-specific API keys
    # By typing them as Optional[str], Pydantic won't crash if they are missing
    # UNLESS we explicitly need them, which we'll check when initializing the LLM.
    GOOGLE_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    
    # Database Configuration (for Phase 6+)
    DATABASE_URL: Optional[str] = None
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Ignore extra environment variables we don't care about
        extra="ignore"
    )

# Create a global instance of Settings that all modules can import
# Usage: from src.config import settings
settings = Settings()
