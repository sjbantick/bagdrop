"""Configuration for BagDrop backend"""
from pydantic_settings import BaseSettings, SettingsConfigDict
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
    public_app_url: str = "http://localhost:3000"
    public_api_url: str = "http://localhost:8000"
    public_listing_freshness_hours: int = 12
    listing_report_auto_hide_threshold: int = 2
    listing_report_stale_quarantine_hours: int = 6
    outbound_utm_source: str = "bagdrop"
    realreal_affiliate_query: str = ""
    vestiaire_affiliate_query: str = ""
    fashionphile_affiliate_query: str = ""
    rebag_affiliate_query: str = ""
    watch_token_secret: str = "bagdrop-dev-watch-secret"
    alert_from_email: str = ""
    alert_reply_to: str = ""
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_username: str = ""
    smtp_password: str = ""
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    intelligence_digest_recipients: str = ""
    watch_alert_max_listings: int = 6
    watch_alert_freshness_hours: int = 168
    watch_alert_cooldown_hours: int = 24
    watch_alert_scheduler_enabled: bool = True
    watch_alert_interval_minutes: int = 30
    intelligence_digest_enabled: bool = False
    intelligence_digest_hour_utc: int = 13
    intelligence_digest_minute_utc: int = 0
    ops_dashboard_token: str = ""

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
    enable_yoogi: bool = True
    enable_luxedh: bool = False
    enable_madisonavenuecouture: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False,
    )


settings = Settings()
