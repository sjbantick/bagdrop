"""Pydantic response/request schemas for BagDrop API."""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ListingResponse(BaseModel):
    id: str
    platform: str
    brand: str
    model: str
    size: Optional[str]
    color: Optional[str]
    condition: str
    current_price: float
    original_price: Optional[float]
    drop_pct: Optional[float]
    drop_amount: Optional[float]
    url: str
    description: Optional[str]
    last_seen: datetime
    first_seen: datetime
    photo_url: Optional[str]
    hardware: Optional[str]

    model_config = ConfigDict(from_attributes=True)


class PaginatedListingsResponse(BaseModel):
    items: List[ListingResponse]
    next_cursor: Optional[str] = None
    has_more: bool = False


class PriceHistoryResponse(BaseModel):
    price: float
    detected_at: datetime
    drop_pct: Optional[float]

    model_config = ConfigDict(from_attributes=True)


class BagIndexResponse(BaseModel):
    brand: str
    index_value: float
    snapshot_date: datetime
    current_avg_price: Optional[float]
    active_listings_count: Optional[int]
    peak_avg_price: Optional[float]
    avg_drop_pct: Optional[float]
    previous_index_value: Optional[float]
    delta_pct: Optional[float]
    trend: str

    model_config = ConfigDict(from_attributes=True)


class PlatformBreakdownResponse(BaseModel):
    platform: str
    listing_count: int


class MarketStatsResponse(BaseModel):
    listing_count: int
    lowest_price: Optional[float]
    average_price: Optional[float]
    average_drop_pct: Optional[float]
    biggest_drop_pct: Optional[float]


class MarketResponse(BaseModel):
    brand: str
    model: str
    canonical_path: str
    stats: MarketStatsResponse
    platform_breakdown: List[PlatformBreakdownResponse]
    listings: List[ListingResponse]


class FeaturedMarketResponse(BaseModel):
    brand: str
    model: str
    canonical_path: str
    listing_count: int
    lowest_price: Optional[float]
    average_drop_pct: Optional[float]
    biggest_drop_pct: Optional[float]


class ArbitrageOpportunityResponse(BaseModel):
    listing: ListingResponse
    canonical_path: str
    market_listing_count: int
    market_platform_count: int
    market_average_price: float
    market_lowest_price: float
    market_gap_amount: float
    market_gap_pct: float


class MarketVelocityResponse(BaseModel):
    brand: str
    model: str
    canonical_path: str
    active_listings: int
    platform_count: int
    recent_listings_7d: int
    recent_listings_30d: int
    recent_listings_60d: int
    recent_listings_90d: int
    velocity_score: float
    velocity_label: str


class NewDropOpportunityResponse(BaseModel):
    listing: ListingResponse
    canonical_path: str
    hours_since_first_seen: float
    significance_score: float
    market_gap_pct: float
    market_platform_count: int


class PlatformOpsResponse(BaseModel):
    platform: str
    last_attempt_at: Optional[datetime]
    last_success_at: Optional[datetime]
    last_listing_sync_at: Optional[datetime]
    last_run_success: Optional[bool]
    stale: bool
    error_message: Optional[str]
    listings_found: Optional[int]
    active_listings: int
    outbound_clicks_24h: int


class OpsSummaryResponse(BaseModel):
    generated_at: datetime
    scrape_interval_hours: int
    stale_after_hours: int
    total_outbound_clicks_24h: int
    active_watch_subscriptions: int
    watch_alert_deliveries_24h: int
    smtp_configured: bool
    watch_alert_scheduler_enabled: bool
    intelligence_digest_enabled: bool
    intelligence_digest_recipient_count: int
    platforms: List[PlatformOpsResponse]


class TopClickedListingResponse(BaseModel):
    listing_id: str
    brand: str
    model: str
    platform: str
    canonical_path: str
    detail_path: str
    current_price: float
    click_count: int


class TopClickedMarketResponse(BaseModel):
    brand: str
    model: str
    canonical_path: str
    click_count: int


class TopClickSurfaceResponse(BaseModel):
    surface: str
    click_count: int
    unique_listings: int
    unique_markets: int


class TopClickContextResponse(BaseModel):
    context: str
    click_count: int


class TopClickPlatformResponse(BaseModel):
    platform: str
    click_count: int
    unique_listings: int
    unique_markets: int


class TopClicksResponse(BaseModel):
    generated_at: datetime
    days: int
    listings: List[TopClickedListingResponse]
    markets: List[TopClickedMarketResponse]
    platforms: List[TopClickPlatformResponse]
    surfaces: List[TopClickSurfaceResponse]
    contexts: List[TopClickContextResponse]


class WatchSubscriptionRequest(BaseModel):
    email: str
    brand: str
    model: str
    source: str = "market_page"
    target_price: Optional[float] = None


class ListingReportRequest(BaseModel):
    reason: str = "sold"
    source: str = "listing_detail"
    notes: Optional[str] = None


class ListingReportResponse(BaseModel):
    listing_id: str
    reason: str
    source: str
    report_count_7d: int
    listing_hidden: bool
    detail: str


class WatchSubscriptionResponse(BaseModel):
    id: int
    email: str
    brand: str
    model: str
    canonical_path: str
    is_active: bool
    already_subscribed: bool
    target_price: Optional[float] = None
    created_at: datetime
    unsubscribe_url: str

    model_config = ConfigDict(from_attributes=True)


class WatchAlertDeliveryResponse(BaseModel):
    subscription_id: int
    email: str
    market: str
    listing_count: int
    subject: str


class WatchAlertRunResponse(BaseModel):
    dry_run: bool
    subscriptions_with_alerts: int
    deliveries: List[WatchAlertDeliveryResponse]


class IntelligenceDigestRunResponse(BaseModel):
    dry_run: bool
    recipient_count: int
    recipients: List[str]
    subject: str
    brief_url: str
    arbitrage_count: int
    new_drop_count: int
    bag_index_count: int


class IntelligenceBriefResponse(BaseModel):
    generated_at: datetime
    arbitrage: List[ArbitrageOpportunityResponse]
    new_drops: List[NewDropOpportunityResponse]
    bag_index_movers: List[BagIndexResponse]


class AdminHydrationResponse(BaseModel):
    platform: str
    requested_handles: int
    listings_found: int
    listings_new: int
    listings_updated: int


class PriceTrendPointResponse(BaseModel):
    week_start: str  # ISO date YYYY-MM-DD
    avg_price: float
    min_price: float
    max_price: float
    data_points: int


class PriceTrendResponse(BaseModel):
    brand: str
    model: str
    canonical_path: str
    trend_direction: str  # "declining", "rising", "stable"
    trend_pct: Optional[float]  # % change recent vs prior
    data_points_total: int
    trend: list  # List of PriceTrendPointResponse dicts


class WeeklyTopBrand(BaseModel):
    brand: str
    listing_count: int
    avg_drop_pct: Optional[float]


class WeeklyDropsResponse(BaseModel):
    week_start: str  # ISO date string YYYY-MM-DD (Monday)
    week_end: str    # ISO date string YYYY-MM-DD (Sunday)
    week_label: str  # e.g. "March 10–16, 2026"
    listing_count: int
    avg_drop_pct: Optional[float]
    top_brands: List[WeeklyTopBrand]
    listings: List[ListingResponse]


class WeekSummary(BaseModel):
    week_start: str
    week_end: str
    week_label: str
    listing_count: int
    avg_drop_pct: Optional[float]


class PlatformCompareResponse(BaseModel):
    platform: str
    listing_count: int
    lowest_price: Optional[float]
    average_price: Optional[float]
    best_drop_pct: Optional[float]
    value_score: float  # 0-100, higher = better deal vs cross-platform avg


class CrossPlatformSummaryResponse(BaseModel):
    total_listings: int
    overall_lowest_price: Optional[float]
    overall_lowest_price_platform: Optional[str]
    price_spread: Optional[float]  # highest avg - lowest avg across platforms
    price_spread_pct: Optional[float]  # spread as % of overall average
    best_value_platform: Optional[str]


class CrossPlatformCompareResponse(BaseModel):
    brand: str
    model: str
    canonical_path: str
    summary: CrossPlatformSummaryResponse
    platforms: List[PlatformCompareResponse]
