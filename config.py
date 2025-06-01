"""
Configuration management for InnerCalm backend.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    app_name: str = "InnerCalm API"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")

    # Database Configuration
    database_url: str = Field(default="sqlite:///./innercalm.db", env="DATABASE_URL")

    # OpenAI Configuration
    openai_api_key: str = Field(..., env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")

    # Hume AI Configuration
    hume_api_key: str = Field(..., env="HUME_API_KEY")
    hume_secret_key: Optional[str] = Field(default=None, env="HUME_SECRET_KEY")

    # Security Configuration
    secret_key: str = Field(default="your-secret-key-change-in-production", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")

    # AI Configuration
    max_conversation_history: int = Field(default=20, env="MAX_CONVERSATION_HISTORY")
    emotion_analysis_threshold: float = Field(default=0.5, env="EMOTION_ANALYSIS_THRESHOLD")
    preload_emotion_model: bool = Field(default=False, env="PRELOAD_EMOTION_MODEL")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields from .env

    @property
    def allowed_origins(self) -> list[str]:
        """Get allowed origins from environment or default."""
        origins_str = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:3001")
        return [origin.strip().strip('"').strip("'") for origin in origins_str.split(",")]


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings
