"""
Configuration management for the FastAPI application.
"""

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Application
    APP_NAME: str = "Medical Work Order Analysis API"
    DEBUG: bool = Field(default=False, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8000, env="PORT")

    # Database
    DB_HOST: str = Field(default="localhost", env="DB_HOST")
    DB_PORT: int = Field(default=5432, env="DB_PORT")
    DB_NAME: str = Field(default="medical_ai_ops", env="DB_NAME")
    DB_USER: str = Field(default="postgres", env="DB_USER")
    DB_PASSWORD: str = Field(default="", env="DB_PASSWORD")
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=10, env="DB_MAX_OVERFLOW")

    # Database URL
    @property
    def DATABASE_URL(self) -> str:
        """Construct database URL from components."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    # API
    API_V1_PREFIX: str = "/api/v1"

    # Security
    SECRET_KEY: str = Field(default="your-secret-key-here", env="SECRET_KEY")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # CORS
    CORS_ORIGINS: list[str] = Field(default=["*"], env="CORS_ORIGINS")

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
