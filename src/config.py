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
    
    # Hugging Face token for private DistilBERT model
    HF_TOKEN: Optional[str] = None
    
    # Database Configuration (for Phase 6+)
    DATABASE_URL: Optional[str] = None
    DATABASE_URL_POOLED: Optional[str] = None

    # RAG / Vector Store Configuration (Phase 7+)
    CHROMA_PERSIST_DIR: str = "data/chroma_db"
    CHROMA_COLLECTION_NAME: str = "security_knowledge_base"
    RAG_EMBEDDING_MODEL: str = "all-MiniLM-L6-v2"
    RAG_TOP_K: int = 3
    RAG_ENABLED: bool = True
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Ignore extra environment variables we don't care about
        extra="ignore"
    )

# Create a global instance of Settings that all modules can import
# Usage: from src.config import settings
settings = Settings()
