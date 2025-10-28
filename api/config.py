"""
Configuration for Central Server API
Loads settings from environment variables with sensible defaults
"""
import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Database
    database_url: str = "mysql+pymysql://securitycam:password@localhost/security_cameras"
    database_pool_size: int = 10
    database_max_overflow: int = 20
    
    # API
    api_host: str = "0.0.0.0"  # Listen on all interfaces
    api_port: int = 8000
    api_reload: bool = False  # Auto-reload on code changes (dev only)
    
    # CORS (allow web UI to call API)
    # Add your central server IP here
    cors_origins: list = ["http://localhost", "http://192.168.1.100"]
    
    # Logging
    log_level: str = "INFO"  # INFO, DEBUG, WARNING, ERROR
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # Ignore extra fields from .env

# Global settings instance
settings = Settings()