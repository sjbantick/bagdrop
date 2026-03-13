"""Database models for BagDrop"""
from datetime import datetime
from enum import Enum
from sqlalchemy import Column, String, Float, Integer, DateTime, Boolean, Index, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class ConditionGrade(str, Enum):
    """Condition grades for handbags"""
    PRISTINE = "pristine"  # Never used, perfect condition
    EXCELLENT = "excellent"  # Like new, barely used
    GOOD = "good"  # Some minor wear
    FAIR = "fair"  # Visible wear, still wearable


class Platform(str, Enum):
    """Supported resale platforms"""
    REALREAL = "realreal"
    VESTIAIRE = "vestiaire"
    FASHIONPHILE = "fashionphile"
    REBAG = "rebag"
    YOOGI = "yoogi"
    COSETTE = "cosette"
    THE_PURSE_AFFAIR = "thepurseaffair"
    LUXEDH = "luxedh"
    MADISON_AVENUE_COUTURE = "madisonavenuecouture"


class Listing(Base):
    """Individual bag listing from a platform"""
    __tablename__ = "listings"

    id = Column(String(255), primary_key=True)  # unique_id = f"{platform}_{listing_id}"

    # Platform metadata
    platform = Column(String(50), nullable=False, index=True)
    platform_id = Column(String(255), nullable=False, index=True)
    url = Column(String(2000), nullable=False)

    # Bag details
    brand = Column(String(100), nullable=False, index=True)
    model = Column(Text, nullable=False, index=True)
    size = Column(String(50))
    color = Column(String(100), index=True)
    hardware = Column(String(100))
    condition = Column(String(50), nullable=False)

    # Pricing
    current_price = Column(Float, nullable=False)
    original_price = Column(Float)  # Last known price on platform
    drop_amount = Column(Float)  # current - original
    drop_pct = Column(Float)  # (drop_amount / original) * 100

    # Metadata
    first_seen = Column(DateTime, nullable=False, default=datetime.utcnow)
    last_seen = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_price_check = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_active = Column(Boolean, default=True, index=True)  # Still listed?

    # Additional details
    description = Column(Text)
    photo_url = Column(String(2000))

    __table_args__ = (
        Index('idx_brand_model', 'brand', 'model'),
        Index('idx_platform_id', 'platform', 'platform_id', unique=True),
        Index('idx_last_seen', 'last_seen'),
        Index('idx_drop_pct', 'drop_pct'),
        # Composite index for the main feed query: WHERE is_active=True ORDER BY drop_pct DESC
        Index('idx_active_drop_pct', 'is_active', 'drop_pct'),
    )


class PriceHistory(Base):
    """Price history for each listing (immutable log)"""
    __tablename__ = "price_history"

    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(String(255), nullable=False, index=True)
    platform = Column(String(50), nullable=False)

    price = Column(Float, nullable=False)
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Only populate if we have this info
    original_price = Column(Float)
    drop_pct = Column(Float)

    __table_args__ = (
        Index('idx_listing_detected', 'listing_id', 'detected_at'),
    )


class BagIndexSnapshot(Base):
    """Weekly BagIndex snapshot — aggregate price health per brand"""
    __tablename__ = "bag_index_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)
    brand = Column(String(100), nullable=False, index=True)

    snapshot_date = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Index value: current avg resale / peak avg resale * 100
    index_value = Column(Float, nullable=False)
    peak_avg_price = Column(Float)  # Historical peak average
    current_avg_price = Column(Float)

    # Stats
    active_listings_count = Column(Integer)
    avg_drop_pct = Column(Float)

    __table_args__ = (
        Index('idx_brand_date', 'brand', 'snapshot_date'),
    )


class VelocityScore(Base):
    """Relisting frequency score — how fast a model is being relisted"""
    __tablename__ = "velocity_scores"

    id = Column(Integer, primary_key=True, autoincrement=True)
    brand = Column(String(100), nullable=False, index=True)
    model = Column(Text, nullable=False, index=True)

    calculated_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    # Number of unique listings in last 30/60/90 days
    relisting_30d = Column(Integer)  # How many times listed in 30 days?
    relisting_60d = Column(Integer)
    relisting_90d = Column(Integer)

    # Velocity score: high = lots of relisting = distress signal
    velocity_score = Column(Float)  # 0-100

    __table_args__ = (
        Index('idx_brand_model_date', 'brand', 'model', 'calculated_at'),
    )


class Scrape(Base):
    """Log of each scrape run"""
    __tablename__ = "scrapes"

    id = Column(Integer, primary_key=True, autoincrement=True)
    platform = Column(String(50), nullable=False, index=True)

    started_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime)

    listings_found = Column(Integer, default=0)
    listings_new = Column(Integer, default=0)
    listings_updated = Column(Integer, default=0)

    success = Column(Boolean, default=False)
    error_message = Column(Text)


class OutboundClick(Base):
    """Tracked outbound marketplace click for attribution and affiliate routing."""
    __tablename__ = "outbound_clicks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(String(255), nullable=False, index=True)
    platform = Column(String(50), nullable=False, index=True)
    surface = Column(String(100), nullable=False, index=True)
    context = Column(String(100))

    target_url = Column(String(2000), nullable=False)
    referer = Column(String(2000))
    user_agent = Column(Text)
    client_ip = Column(String(128), index=True)

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_outbound_listing_surface', 'listing_id', 'surface', 'created_at'),
    )


class ListingReport(Base):
    """User-reported listing quality issue for trust and stale inventory cleanup."""
    __tablename__ = "listing_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(String(255), nullable=False, index=True)
    platform = Column(String(50), nullable=False, index=True)
    reason = Column(String(50), nullable=False, index=True)
    source = Column(String(100), nullable=False, default="unknown")
    notes = Column(Text)

    reporter_ip = Column(String(128), index=True)
    user_agent = Column(Text)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_listing_report_listing_reason', 'listing_id', 'reason', 'created_at'),
    )


class WatchSubscription(Base):
    """Email-based market watch intent captured before full alerting is built."""
    __tablename__ = "watch_subscriptions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), nullable=False, index=True)
    brand = Column(String(100), nullable=False, index=True)
    model = Column(Text, nullable=False, index=True)
    brand_slug = Column(String(120), nullable=False, index=True)
    model_slug = Column(String(120), nullable=False, index=True)
    source = Column(String(100), nullable=False, default="unknown")

    is_active = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_notified_at = Column(DateTime)

    __table_args__ = (
        Index('idx_watch_email_market', 'email', 'brand_slug', 'model_slug', unique=True),
        Index('idx_watch_market', 'brand_slug', 'model_slug', 'is_active'),
    )


class WatchAlertDelivery(Base):
    """Delivery log so BagDrop only alerts new listings once per watch subscription."""
    __tablename__ = "watch_alert_deliveries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    watch_subscription_id = Column(Integer, nullable=False, index=True)
    listing_id = Column(String(255), nullable=False, index=True)
    email = Column(String(255), nullable=False, index=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index('idx_watch_delivery_unique', 'watch_subscription_id', 'listing_id', unique=True),
    )
