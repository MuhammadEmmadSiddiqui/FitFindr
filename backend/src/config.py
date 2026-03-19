"""Configuration management for FitFindr application"""
import os
from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Application
    APP_NAME: str = "FitFindr"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # API Keys (loaded from environment)
    GROQ_API_KEYS: str = ""
    
    # Model Configuration
    BERT_MODEL: str = "bert-base-uncased"
    LLM_MODEL: str = "llama-3.3-70b-versatile"
    LLM_TEMPERATURE: float = 0.0
    LLM_MAX_TOKENS: int = 1024
    LLM_TOP_P: float = 0.65
    
    # Database
    DATABASE_URL: str = "sqlite:///./data/fitfindr.db"

    # Authentication (JWT)
    SECRET_KEY: str = "change-me-in-production-use-a-long-random-string"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    # Paths  (config.py lives at backend/src/config.py → 3 levels up = project root)
    BASE_DIR: Path = Path(__file__).parents[2]
    DATA_DIR: Path = BASE_DIR / "data"
    LOGS_DIR: Path = BASE_DIR / "logs"
    UPLOAD_DIR: Path = DATA_DIR / "uploads"
    
    # Streamlit
    STREAMLIT_PORT: int = 8501
    
    # FastAPI
    API_PORT: int = 8000
    API_HOST: str = "0.0.0.0"
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FILE: str = "fitfindr.log"

    # LangSmith observability (optional — tracing is disabled when LANGCHAIN_API_KEY is empty)
    # Set LANGCHAIN_TRACING_V2 is managed automatically in graph_service._configure_langsmith()
    LANGCHAIN_API_KEY: str = ""
    LANGCHAIN_PROJECT: str = "fitfindr"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
    
    def get_api_keys(self) -> List[str]:
        """Parse API keys from comma-separated string"""
        if not self.GROQ_API_KEYS:
            return []
        return [key.strip() for key in self.GROQ_API_KEYS.split(",") if key.strip()]
    
    def ensure_directories(self):
        """Create necessary directories if they don't exist"""
        self.DATA_DIR.mkdir(parents=True, exist_ok=True)
        self.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings = Settings()
settings.ensure_directories()
