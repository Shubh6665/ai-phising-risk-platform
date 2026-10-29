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
    # Primary: Google AI Studio (Gemini 3.8 Flash)
    LLM_PROVIDER: str = "google"
    LLM_MODEL: str = "gemini-3.8-flash"
    
    # Fallback: Groq (OpenAI GPT-OSS 120B)
    FALLBACK_LLM_PROVIDER: str = "groq"
    FALLBACK_LLM_MODEL: str = "openai/gpt-oss-120b"
    
    # Generation parameters
    LLM_TEMPERATURE: float = 0.1
    LLM_TIMEOUT_SECONDS: float = 30.0
    LLM_MAX_TOKENS: int = 1024
    LLM_ENABLED: bool = True
    
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

    # CORS Configuration (Phase 9)
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        # Ignore extra environment variables we don't care about
        extra="ignore"
    )

# Create a global instance of Settings that all modules can import
# Usage: from src.config import settings
settings = Settings()
