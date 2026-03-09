"""Configuration for BagDrop backend"""
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """App settings from environment"""

    # Database
    database_url: str = "sqlite:///./bagdrop.db"  # Default to SQLite for dev

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True

    # Scraping
    scraper_timeout: int = 30
    scraper_retry_count: int = 3
    scraper_rate_limit_delay: float = 1.0  # seconds between requests

    # Scheduler
    scheduler_enabled: bool = True
    scraper_interval_hours: int = 4

    # Features
    enable_realreal: bool = True
    enable_vestiaire: bool = True
    enable_fashionphile: bool = True
    enable_rebag: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
