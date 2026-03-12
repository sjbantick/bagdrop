"""BagDrop FastAPI backend"""
from contextlib import asynccontextmanager
from datetime import datetime, timedelta
import asyncio
import re
from typing import List, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, ConfigDict
from sqlalchemy import desc, and_, func
from sqlalchemy.orm import Session

from alerts import build_watch_unsubscribe_url, deliver_watch_alerts, resolve_watch_unsubscribe_token
from database import get_db, init_db
from intelligence import compute_bag_index_rows, persist_bag_index_snapshots
from models import (
    Listing,
    PriceHistory,
    BagIndexSnapshot,
    OutboundClick,
    ListingReport,
    Scrape,
    Platform,
    WatchSubscription,
    WatchAlertDelivery,
)
from config import settings
from scheduler import create_scheduler, run_all_scrapers, run_scraper
from utils import market_path, slugify_text

scheduler = create_scheduler()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    print("Database initialized")
    scheduler.start()
    print("Scheduler started — scraping every 4 hours")
    asyncio.create_task(run_all_scrapers())
    try:
        yield
    finally:
        scheduler.shutdown(wait=False)


app = FastAPI(title="BagDrop API", version="0.1.0", lifespan=lifespan)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Pydantic models
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


def _round_float(value: Optional[float], digits: int = 1) -> Optional[float]:
    if value is None:
        return None
    return round(float(value), digits)


def _public_listing_cutoff() -> datetime:
    return datetime.utcnow() - timedelta(hours=max(settings.public_listing_freshness_hours, 1))


def _public_listing_condition(*conditions):
    return and_(
        Listing.is_active == True,
        Listing.last_seen >= _public_listing_cutoff(),
        *conditions,
    )


def _normalize_listing_report_reason(value: str) -> str:
    normalized = (value or "").strip().lower()
    allowed = {"sold", "dead", "broken"}
    if normalized not in allowed:
        raise HTTPException(status_code=400, detail="Invalid listing report reason")
    return normalized


def _normalize_listing_report_notes(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    return normalized[:500]


def _resolve_market(db: Session, brand_slug: str, model_slug: str) -> Optional[tuple[str, str]]:
    combinations = (
        db.query(Listing.brand, Listing.model)
        .filter(_public_listing_condition())
        .distinct()
        .all()
    )
    for brand, model in combinations:
        if slugify_text(brand) == brand_slug and slugify_text(model) == model_slug:
            return brand, model
    return None


def _render_affiliate_template(value: str, replacements: Optional[dict[str, str]] = None) -> str:
    if not replacements:
        return value

    def replace(match: re.Match[str]) -> str:
        return str(replacements.get(match.group(1), ""))

    return re.sub(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", replace, value)


def _affiliate_query_for_platform(
    platform: str,
    replacements: Optional[dict[str, str]] = None,
) -> dict[str, str]:
    query_string = {
        "realreal": settings.realreal_affiliate_query,
        "vestiaire": settings.vestiaire_affiliate_query,
        "fashionphile": settings.fashionphile_affiliate_query,
        "rebag": settings.rebag_affiliate_query,
    }.get(platform, "")

    normalized = query_string.lstrip("?").strip()
    if not normalized:
        return {}

    params = dict(parse_qsl(normalized, keep_blank_values=True))
    return {
        key: _render_affiliate_template(value, replacements)
        for key, value in params.items()
    }


def _build_outbound_target_url(listing: Listing, surface: str, context: Optional[str] = None) -> str:
    split = urlsplit(listing.url)
    query = dict(parse_qsl(split.query, keep_blank_values=True))
    replacements = {
        "brand": listing.brand or "",
        "brand_slug": slugify_text(listing.brand or ""),
        "context": context or "",
        "listing_id": listing.id or "",
        "market_slug": f"{slugify_text(listing.brand or '')}/{slugify_text(listing.model or '')}",
        "model": listing.model or "",
        "model_slug": slugify_text(listing.model or ""),
        "platform": listing.platform or "",
        "platform_id": listing.platform_id or "",
        "surface": surface or "",
        "utm_source": settings.outbound_utm_source,
    }
    query.update(_affiliate_query_for_platform(listing.platform, replacements))
    query.setdefault("utm_source", settings.outbound_utm_source)
    query.setdefault("utm_medium", "marketplace_click")
    query.setdefault("utm_campaign", listing.platform)
    query["utm_content"] = surface
    if context:
        query["utm_term"] = context

    return urlunsplit((
        split.scheme,
        split.netloc,
        split.path,
        urlencode(query, doseq=True),
        split.fragment,
    ))


def _platforms_to_monitor() -> List[str]:
    return [platform.value for platform in Platform]


def _normalize_watch_email(email: str) -> str:
    normalized = (email or "").strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
        raise HTTPException(status_code=400, detail="A valid email address is required")
    return normalized


def _require_ops_access(
    token: Optional[str] = Query(None),
    x_ops_token: Optional[str] = Header(None, alias="x-ops-token"),
):
    expected = (settings.ops_dashboard_token or "").strip()
    if not expected:
        if settings.debug:
            return
        raise HTTPException(status_code=404, detail="Not found")

    actual = (token or x_ops_token or "").strip()
    if actual != expected:
        raise HTTPException(status_code=404, detail="Not found")


def _velocity_label(score: float) -> str:
    if score >= 75:
        return "hot"
    if score >= 45:
        return "active"
    if score >= 20:
        return "stable"
    return "slow"


def _build_market_velocity(db: Session, brand: str, model: str) -> MarketVelocityResponse:
    now = datetime.utcnow()
    windows = {
        "7d": now - timedelta(days=7),
        "30d": now - timedelta(days=30),
        "60d": now - timedelta(days=60),
        "90d": now - timedelta(days=90),
    }

    base_query = db.query(Listing).filter(
        _public_listing_condition(
            Listing.brand == brand,
            Listing.model == model,
        )
    )

    active_listings = base_query.count()
    platform_count = (
        db.query(func.count(func.distinct(Listing.platform)))
        .filter(
            and_(
                Listing.is_active == True,
                Listing.brand == brand,
                Listing.model == model,
            )
        )
        .scalar()
        or 0
    )

    recent_counts = {}
    for label, cutoff in windows.items():
        recent_counts[label] = (
            db.query(func.count(Listing.id))
            .filter(
                and_(
                    Listing.is_active == True,
                    Listing.brand == brand,
                    Listing.model == model,
                    Listing.first_seen >= cutoff,
                )
            )
            .scalar()
            or 0
        )

    freshness_ratio_30d = recent_counts["30d"] / active_listings if active_listings else 0
    freshness_ratio_7d = recent_counts["7d"] / active_listings if active_listings else 0
    platform_factor = min(platform_count / 4, 1)
    velocity_score = min(
        100.0,
        round((freshness_ratio_30d * 55 + freshness_ratio_7d * 30 + platform_factor * 15) * 100, 1),
    )

    return MarketVelocityResponse(
        brand=brand,
        model=model,
        canonical_path=market_path(brand, model),
        active_listings=active_listings,
        platform_count=platform_count,
        recent_listings_7d=recent_counts["7d"],
        recent_listings_30d=recent_counts["30d"],
        recent_listings_60d=recent_counts["60d"],
        recent_listings_90d=recent_counts["90d"],
        velocity_score=velocity_score,
        velocity_label=_velocity_label(velocity_score),
    )


def _build_arbitrage_opportunities(
    db: Session,
    *,
    limit: int = 12,
    min_market_listings: int = 3,
    min_platforms: int = 2,
    min_gap_pct: float = 12.0,
) -> List[ArbitrageOpportunityResponse]:
    market_stats = (
        db.query(
            Listing.brand.label("brand"),
            Listing.model.label("model"),
            func.count(Listing.id).label("listing_count"),
            func.count(func.distinct(Listing.platform)).label("platform_count"),
            func.avg(Listing.current_price).label("average_price"),
            func.min(Listing.current_price).label("lowest_price"),
        )
        .filter(Listing.is_active == True)
        .filter(Listing.last_seen >= _public_listing_cutoff())
        .group_by(Listing.brand, Listing.model)
        .having(func.count(Listing.id) >= min_market_listings)
        .having(func.count(func.distinct(Listing.platform)) >= min_platforms)
        .subquery()
    )

    rows = (
        db.query(
            Listing,
            market_stats.c.listing_count.label("market_listing_count"),
            market_stats.c.platform_count.label("market_platform_count"),
            market_stats.c.average_price.label("market_average_price"),
            market_stats.c.lowest_price.label("market_lowest_price"),
        )
        .join(
            market_stats,
            and_(
                Listing.brand == market_stats.c.brand,
                Listing.model == market_stats.c.model,
            ),
        )
        .filter(Listing.is_active == True)
        .filter(Listing.current_price < market_stats.c.average_price)
        .filter(
            ((market_stats.c.average_price - Listing.current_price) / market_stats.c.average_price * 100)
            >= min_gap_pct
        )
        .order_by(
            desc((market_stats.c.average_price - Listing.current_price) / market_stats.c.average_price),
            desc(Listing.drop_pct),
            Listing.current_price,
        )
        .limit(limit)
        .all()
    )

    opportunities: List[ArbitrageOpportunityResponse] = []
    for listing, market_listing_count, market_platform_count, market_average_price, market_lowest_price in rows:
        market_gap_amount = float(market_average_price) - float(listing.current_price)
        market_gap_pct = (market_gap_amount / float(market_average_price)) * 100 if market_average_price else 0
        opportunities.append(
            ArbitrageOpportunityResponse(
                listing=listing,
                canonical_path=market_path(listing.brand, listing.model),
                market_listing_count=int(market_listing_count),
                market_platform_count=int(market_platform_count),
                market_average_price=_round_float(market_average_price, 0) or 0,
                market_lowest_price=_round_float(market_lowest_price, 0) or 0,
                market_gap_amount=_round_float(market_gap_amount, 0) or 0,
                market_gap_pct=_round_float(market_gap_pct) or 0,
            )
        )

    return opportunities


def _build_new_drop_opportunities(
    db: Session,
    *,
    hours: int = 72,
    limit: int = 12,
    min_significance: float = 35.0,
) -> List[NewDropOpportunityResponse]:
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    market_stats = (
        db.query(
            Listing.brand.label("brand"),
            Listing.model.label("model"),
            func.avg(Listing.current_price).label("average_price"),
            func.count(func.distinct(Listing.platform)).label("platform_count"),
        )
        .filter(Listing.is_active == True)
        .filter(Listing.last_seen >= _public_listing_cutoff())
        .group_by(Listing.brand, Listing.model)
        .subquery()
    )

    recent_listings = (
        db.query(
            Listing,
            market_stats.c.average_price.label("market_average_price"),
            market_stats.c.platform_count.label("market_platform_count"),
        )
        .join(
            market_stats,
            and_(
                Listing.brand == market_stats.c.brand,
                Listing.model == market_stats.c.model,
            ),
        )
        .filter(Listing.is_active == True, Listing.first_seen >= cutoff)
        .filter(Listing.last_seen >= _public_listing_cutoff())
        .order_by(desc(Listing.first_seen), desc(Listing.drop_pct))
        .all()
    )

    opportunities: List[NewDropOpportunityResponse] = []
    now = datetime.utcnow()
    for listing, market_average_price, market_platform_count in recent_listings:
        hours_since_first_seen = max((now - listing.first_seen).total_seconds() / 3600, 0.0)
        recency_score = max(0.0, 1 - (hours_since_first_seen / hours))
        drop_score = min((listing.drop_pct or 0) / 40, 1.0)
        market_gap_pct = 0.0
        if market_average_price and listing.current_price < market_average_price:
            market_gap_pct = ((float(market_average_price) - float(listing.current_price)) / float(market_average_price)) * 100
        gap_score = min(max(market_gap_pct, 0.0) / 25, 1.0)
        platform_score = min(max((int(market_platform_count or 1) - 1) / 3, 0.0), 1.0)
        significance_score = round((drop_score * 40 + recency_score * 35 + gap_score * 15 + platform_score * 10) * 100 / 100, 1)

        if significance_score < min_significance:
            continue

        opportunities.append(
            NewDropOpportunityResponse(
                listing=listing,
                canonical_path=market_path(listing.brand, listing.model),
                hours_since_first_seen=round(hours_since_first_seen, 1),
                significance_score=significance_score,
                market_gap_pct=_round_float(market_gap_pct) or 0,
                market_platform_count=int(market_platform_count or 1),
            )
        )

    opportunities.sort(key=lambda item: (-item.significance_score, item.hours_since_first_seen))
    return opportunities[:limit]


def _build_intelligence_brief(
    db: Session,
    *,
    arbitrage_limit: int = 6,
    new_drop_limit: int = 6,
    bag_index_limit: int = 6,
) -> IntelligenceBriefResponse:
    bag_index_rows = compute_bag_index_rows(db, limit=max(bag_index_limit * 2, bag_index_limit), min_active_listings=2)
    ranked_bag_index = sorted(
        bag_index_rows,
        key=lambda row: (
            0 if row.delta_pct is None else abs(row.delta_pct),
            row.active_listings_count,
        ),
        reverse=True,
    )[:bag_index_limit]

    return IntelligenceBriefResponse(
        generated_at=datetime.utcnow(),
        arbitrage=_build_arbitrage_opportunities(db, limit=arbitrage_limit, min_market_listings=3, min_platforms=2, min_gap_pct=12),
        new_drops=_build_new_drop_opportunities(db, hours=72, limit=new_drop_limit, min_significance=35),
        bag_index_movers=[BagIndexResponse(**row.__dict__) for row in ranked_bag_index],
    )


def _build_top_clicks(
    db: Session,
    *,
    days: int = 7,
    limit: int = 10,
) -> TopClicksResponse:
    cutoff = datetime.utcnow() - timedelta(days=days)

    listing_rows = (
        db.query(
            OutboundClick.listing_id.label("listing_id"),
            func.count(OutboundClick.id).label("click_count"),
            Listing.brand.label("brand"),
            Listing.model.label("model"),
            Listing.platform.label("platform"),
            Listing.current_price.label("current_price"),
        )
        .join(Listing, Listing.id == OutboundClick.listing_id)
        .filter(OutboundClick.created_at >= cutoff)
        .group_by(
            OutboundClick.listing_id,
            Listing.brand,
            Listing.model,
            Listing.platform,
            Listing.current_price,
        )
        .order_by(desc(func.count(OutboundClick.id)), Listing.brand, Listing.model)
        .limit(limit)
        .all()
    )

    market_rows = (
        db.query(
            Listing.brand.label("brand"),
            Listing.model.label("model"),
            func.count(OutboundClick.id).label("click_count"),
        )
        .join(Listing, Listing.id == OutboundClick.listing_id)
        .filter(OutboundClick.created_at >= cutoff)
        .group_by(Listing.brand, Listing.model)
        .order_by(desc(func.count(OutboundClick.id)), Listing.brand, Listing.model)
        .limit(limit)
        .all()
    )

    platform_rows = (
        db.query(
            Listing.platform.label("platform"),
            func.count(OutboundClick.id).label("click_count"),
            func.count(func.distinct(OutboundClick.listing_id)).label("unique_listings"),
            func.count(func.distinct(Listing.brand + "|" + Listing.model)).label("unique_markets"),
        )
        .join(Listing, Listing.id == OutboundClick.listing_id)
        .filter(OutboundClick.created_at >= cutoff)
        .group_by(Listing.platform)
        .order_by(desc(func.count(OutboundClick.id)), Listing.platform)
        .limit(limit)
        .all()
    )

    surface_rows = (
        db.query(
            OutboundClick.surface.label("surface"),
            func.count(OutboundClick.id).label("click_count"),
            func.count(func.distinct(OutboundClick.listing_id)).label("unique_listings"),
            func.count(func.distinct(Listing.brand + "|" + Listing.model)).label("unique_markets"),
        )
        .join(Listing, Listing.id == OutboundClick.listing_id)
        .filter(OutboundClick.created_at >= cutoff)
        .group_by(OutboundClick.surface)
        .order_by(desc(func.count(OutboundClick.id)), OutboundClick.surface)
        .limit(limit)
        .all()
    )

    context_rows = (
        db.query(
            OutboundClick.context.label("context"),
            func.count(OutboundClick.id).label("click_count"),
        )
        .filter(
            and_(
                OutboundClick.created_at >= cutoff,
                OutboundClick.context.isnot(None),
                OutboundClick.context != "",
            )
        )
        .group_by(OutboundClick.context)
        .order_by(desc(func.count(OutboundClick.id)), OutboundClick.context)
        .limit(limit)
        .all()
    )

    return TopClicksResponse(
        generated_at=datetime.utcnow(),
        days=days,
        listings=[
            TopClickedListingResponse(
                listing_id=row.listing_id,
                brand=row.brand,
                model=row.model,
                platform=row.platform,
                canonical_path=market_path(row.brand, row.model),
                detail_path=f"/listings/{row.listing_id}",
                current_price=float(row.current_price or 0),
                click_count=int(row.click_count or 0),
            )
            for row in listing_rows
        ],
        markets=[
            TopClickedMarketResponse(
                brand=row.brand,
                model=row.model,
                canonical_path=market_path(row.brand, row.model),
                click_count=int(row.click_count or 0),
            )
            for row in market_rows
        ],
        platforms=[
            TopClickPlatformResponse(
                platform=row.platform,
                click_count=int(row.click_count or 0),
                unique_listings=int(row.unique_listings or 0),
                unique_markets=int(row.unique_markets or 0),
            )
            for row in platform_rows
        ],
        surfaces=[
            TopClickSurfaceResponse(
                surface=row.surface,
                click_count=int(row.click_count or 0),
                unique_listings=int(row.unique_listings or 0),
                unique_markets=int(row.unique_markets or 0),
            )
            for row in surface_rows
        ],
        contexts=[
            TopClickContextResponse(
                context=row.context,
                click_count=int(row.click_count or 0),
            )
            for row in context_rows
        ],
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


@app.get("/api/listings", response_model=List[ListingResponse])
async def get_listings(
    db: Session = Depends(get_db),
    brand: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    min_drop_pct: Optional[float] = Query(0),
    max_drop_pct: Optional[float] = Query(100),
    sort_by: str = Query("drop_pct", pattern="^(drop_pct|drop_amount|current_price|last_seen)$"),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
):
    """Get listings with optional filters. Sorted by biggest drop by default."""
    query = db.query(Listing).filter(Listing.is_active == True)
    query = query.filter(Listing.last_seen >= _public_listing_cutoff())

    if brand:
        query = query.filter(Listing.brand.ilike(f"%{brand}%"))
    if model:
        query = query.filter(Listing.model.ilike(f"%{model}%"))
    if platform:
        query = query.filter(Listing.platform == platform)

    # Filter by drop percentage
    if min_drop_pct is not None or max_drop_pct is not None:
        if min_drop_pct is not None:
            query = query.filter(Listing.drop_pct >= min_drop_pct)
        if max_drop_pct is not None:
            query = query.filter(Listing.drop_pct <= max_drop_pct)

    # Sort
    if sort_by == "drop_pct":
        query = query.order_by(desc(Listing.drop_pct))
    elif sort_by == "drop_amount":
        query = query.order_by(desc(Listing.drop_amount))
    elif sort_by == "current_price":
        query = query.order_by(desc(Listing.current_price))
    elif sort_by == "last_seen":
        query = query.order_by(desc(Listing.last_seen))

    listings = query.limit(limit).offset(offset).all()

    return listings


@app.get("/api/listings/{listing_id}", response_model=ListingResponse)
async def get_listing(listing_id: str, db: Session = Depends(get_db)):
    """Get a specific listing"""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if not listing.is_active or listing.last_seen < _public_listing_cutoff():
        if listing.is_active:
            listing.is_active = False
            db.commit()
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@app.get("/api/listings/{listing_id}/price-history", response_model=List[PriceHistoryResponse])
async def get_listing_price_history(listing_id: str, db: Session = Depends(get_db)):
    """Get price history for a listing"""
    history = (
        db.query(PriceHistory)
        .filter(PriceHistory.listing_id == listing_id)
        .order_by(PriceHistory.detected_at)
        .all()
    )
    return history


@app.get("/api/brands")
async def get_brands(db: Session = Depends(get_db)):
    """Get all unique brands"""
    brands = (
        db.query(Listing.brand)
        .filter(_public_listing_condition())
        .distinct()
        .order_by(Listing.brand)
        .all()
    )
    return [b[0] for b in brands]


@app.get("/api/brands/{brand}/models")
async def get_models_for_brand(brand: str, db: Session = Depends(get_db)):
    """Get all models for a brand"""
    models = (
        db.query(Listing.model)
        .filter(_public_listing_condition(Listing.brand.ilike(brand)))
        .distinct()
        .order_by(Listing.model)
        .all()
    )
    return [m[0] for m in models]


@app.get("/api/new-drops", response_model=List[ListingResponse])
async def get_new_drops(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db),
):
    """Get new drops in the last N hours (detected_at in price_history)"""
    time_cutoff = datetime.utcnow() - timedelta(hours=hours)

    # Get listing IDs that have price history in the last N hours
    recent_listing_ids = (
        db.query(PriceHistory.listing_id)
        .filter(PriceHistory.detected_at >= time_cutoff)
        .distinct()
        .all()
    )
    listing_ids = [lid[0] for lid in recent_listing_ids]

    if not listing_ids:
        return []

    listings = (
        db.query(Listing)
        .filter(_public_listing_condition(Listing.id.in_(listing_ids)))
        .order_by(desc(Listing.drop_pct))
        .limit(limit)
        .all()
    )
    return listings


@app.get("/api/bag-index", response_model=List[BagIndexResponse])
async def get_bag_index(
    limit: int = Query(20, le=100),
    days: int = Query(7, ge=1, le=90),
    live: bool = Query(True),
    min_active_listings: int = Query(2, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """Get latest BagIndex for top brands."""
    if live:
        rows = compute_bag_index_rows(db, limit=limit, min_active_listings=min_active_listings)
        return [BagIndexResponse(**row.__dict__) for row in rows]

    time_cutoff = datetime.utcnow() - timedelta(days=days)

    snapshots = (
        db.query(BagIndexSnapshot)
        .filter(BagIndexSnapshot.snapshot_date >= time_cutoff)
        .order_by(desc(BagIndexSnapshot.snapshot_date), BagIndexSnapshot.index_value)
        .limit(limit)
        .all()
    )
    return snapshots


@app.post("/api/admin/bag-index/recompute", response_model=List[BagIndexResponse])
async def recompute_bag_index(
    limit: int = Query(20, ge=1, le=100),
    min_active_listings: int = Query(2, ge=1, le=20),
    persist: bool = Query(True),
    db: Session = Depends(get_db),
):
    """Recompute current brand-level BagIndex values and optionally persist snapshots."""
    rows = (
        persist_bag_index_snapshots(db, limit=limit, min_active_listings=min_active_listings)
        if persist
        else compute_bag_index_rows(db, limit=limit, min_active_listings=min_active_listings)
    )
    return [BagIndexResponse(**row.__dict__) for row in rows]


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get overall stats for the header display"""
    avg_drop = db.query(func.avg(Listing.drop_pct)).filter(
        _public_listing_condition(Listing.drop_pct > 0)
    ).scalar()
    total_active = db.query(func.count(Listing.id)).filter(_public_listing_condition()).scalar() or 0
    biggest_drop = db.query(func.max(Listing.drop_pct)).filter(_public_listing_condition()).scalar()
    return {
        "total_active_listings": total_active,
        "avg_drop_pct": round(float(avg_drop), 1) if avg_drop else None,
        "biggest_drop_pct": round(float(biggest_drop), 1) if biggest_drop else None,
    }


@app.get("/api/markets/featured", response_model=List[FeaturedMarketResponse])
async def get_featured_markets(
    limit: int = Query(12, ge=1, le=48),
    min_listings: int = Query(2, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get high-signal brand/model markets to surface on the homepage."""
    listing_count = func.count(Listing.id)
    lowest_price = func.min(Listing.current_price)
    average_drop_pct = func.avg(Listing.drop_pct)
    biggest_drop_pct = func.max(Listing.drop_pct)

    rows = (
        db.query(
            Listing.brand.label("brand"),
            Listing.model.label("model"),
            listing_count.label("listing_count"),
            lowest_price.label("lowest_price"),
            average_drop_pct.label("average_drop_pct"),
            biggest_drop_pct.label("biggest_drop_pct"),
        )
        .filter(_public_listing_condition())
        .group_by(Listing.brand, Listing.model)
        .having(listing_count >= min_listings)
        .order_by(desc(listing_count), desc(biggest_drop_pct), Listing.brand, Listing.model)
        .limit(limit)
        .all()
    )

    return [
        FeaturedMarketResponse(
            brand=row.brand,
            model=row.model,
            canonical_path=market_path(row.brand, row.model),
            listing_count=row.listing_count,
            lowest_price=_round_float(row.lowest_price, 0),
            average_drop_pct=_round_float(row.average_drop_pct),
            biggest_drop_pct=_round_float(row.biggest_drop_pct),
        )
        for row in rows
    ]


@app.get("/api/opportunities/arbitrage", response_model=List[ArbitrageOpportunityResponse])
async def get_arbitrage_opportunities(
    limit: int = Query(12, ge=1, le=48),
    min_market_listings: int = Query(3, ge=2, le=20),
    min_platforms: int = Query(2, ge=2, le=8),
    min_gap_pct: float = Query(12.0, ge=5.0, le=80.0),
    db: Session = Depends(get_db),
):
    """Surface listings materially below the live market average for the same brand/model."""
    return _build_arbitrage_opportunities(
        db,
        limit=limit,
        min_market_listings=min_market_listings,
        min_platforms=min_platforms,
        min_gap_pct=min_gap_pct,
    )


@app.get("/api/opportunities/new-drops", response_model=List[NewDropOpportunityResponse])
async def get_new_drop_opportunities(
    hours: int = Query(72, ge=6, le=168),
    limit: int = Query(12, ge=1, le=48),
    min_significance: float = Query(35.0, ge=5.0, le=95.0),
    db: Session = Depends(get_db),
):
    """High-signal new drops ranked by freshness, markdown, and market context."""
    return _build_new_drop_opportunities(
        db,
        hours=hours,
        limit=limit,
        min_significance=min_significance,
    )


@app.get("/api/intelligence/brief", response_model=IntelligenceBriefResponse)
async def get_intelligence_brief(db: Session = Depends(get_db)):
    """Combined daily intelligence payload for owned BagDrop editorial surfaces."""
    return _build_intelligence_brief(db)


@app.get("/api/markets/{brand_slug}/{model_slug}/velocity", response_model=MarketVelocityResponse)
async def get_market_velocity(
    brand_slug: str,
    model_slug: str,
    db: Session = Depends(get_db),
):
    """Estimate market supply velocity from recent listing first-seen activity."""
    resolved = _resolve_market(db, brand_slug, model_slug)
    if not resolved:
        raise HTTPException(status_code=404, detail="Market not found")

    brand, model = resolved
    return _build_market_velocity(db, brand, model)


@app.get("/api/markets/{brand_slug}/{model_slug}", response_model=MarketResponse)
async def get_market_page(
    brand_slug: str,
    model_slug: str,
    limit: int = Query(36, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Resolve a canonical market page for a brand/model pair."""
    resolved = _resolve_market(db, brand_slug, model_slug)
    if not resolved:
        raise HTTPException(status_code=404, detail="Market not found")

    brand, model = resolved
    base_query = db.query(Listing).filter(
        _public_listing_condition(
            Listing.brand == brand,
            Listing.model == model,
        )
    )

    listings = (
        base_query
        .order_by(desc(Listing.drop_pct), Listing.current_price, desc(Listing.last_seen))
        .limit(limit)
        .all()
    )

    stats_row = (
        db.query(
            func.count(Listing.id).label("listing_count"),
            func.min(Listing.current_price).label("lowest_price"),
            func.avg(Listing.current_price).label("average_price"),
            func.avg(Listing.drop_pct).label("average_drop_pct"),
            func.max(Listing.drop_pct).label("biggest_drop_pct"),
        )
        .filter(
            _public_listing_condition(
                Listing.brand == brand,
                Listing.model == model,
            )
        )
        .one()
    )

    platform_listing_count = func.count(Listing.id)
    platform_rows = (
        db.query(
            Listing.platform.label("platform"),
            platform_listing_count.label("listing_count"),
        )
        .filter(
            _public_listing_condition(
                Listing.brand == brand,
                Listing.model == model,
            )
        )
        .group_by(Listing.platform)
        .order_by(desc(platform_listing_count), Listing.platform)
        .all()
    )

    return MarketResponse(
        brand=brand,
        model=model,
        canonical_path=market_path(brand, model),
        stats=MarketStatsResponse(
            listing_count=stats_row.listing_count or 0,
            lowest_price=_round_float(stats_row.lowest_price, 0),
            average_price=_round_float(stats_row.average_price, 0),
            average_drop_pct=_round_float(stats_row.average_drop_pct),
            biggest_drop_pct=_round_float(stats_row.biggest_drop_pct),
        ),
        platform_breakdown=[
            PlatformBreakdownResponse(
                platform=row.platform,
                listing_count=row.listing_count,
            )
            for row in platform_rows
        ],
        listings=listings,
    )


@app.get("/api/listings/{listing_id}/outbound")
async def track_outbound_click(
    listing_id: str,
    request: Request,
    surface: str = Query("unknown", min_length=1, max_length=100),
    context: Optional[str] = Query(None, max_length=100),
    db: Session = Depends(get_db),
):
    """Track an outbound click then redirect to the marketplace listing."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if listing and (not listing.is_active or listing.last_seen < _public_listing_cutoff()):
        listing.is_active = False
        db.commit()
        raise HTTPException(status_code=410, detail="Listing is no longer active")
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    target_url = _build_outbound_target_url(listing, surface=surface, context=context)
    click = OutboundClick(
        listing_id=listing.id,
        platform=listing.platform,
        surface=surface,
        context=context,
        target_url=target_url,
        referer=request.headers.get("referer"),
        user_agent=request.headers.get("user-agent"),
    )
    db.add(click)
    db.commit()

    return RedirectResponse(url=target_url, status_code=307)


@app.post("/api/listings/{listing_id}/report", response_model=ListingReportResponse)
async def report_listing_issue(
    listing_id: str,
    payload: ListingReportRequest,
    request: Request,
    db: Session = Depends(get_db),
):
    """Capture dead-listing feedback and quarantine suspicious inventory quickly."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")

    reason = _normalize_listing_report_reason(payload.reason)
    source = (payload.source or "unknown").strip()[:100] or "unknown"
    notes = _normalize_listing_report_notes(payload.notes)

    report = ListingReport(
        listing_id=listing.id,
        platform=listing.platform,
        reason=reason,
        source=source,
        notes=notes,
        reporter_ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    db.add(report)
    db.flush()

    report_cutoff = datetime.utcnow() - timedelta(days=7)
    report_count_7d = (
        db.query(func.count(ListingReport.id))
        .filter(
            and_(
                ListingReport.listing_id == listing.id,
                ListingReport.created_at >= report_cutoff,
            )
        )
        .scalar()
        or 0
    )

    stale_quarantine_cutoff = datetime.utcnow() - timedelta(
        hours=max(settings.listing_report_stale_quarantine_hours, 1)
    )
    should_hide = report_count_7d >= max(settings.listing_report_auto_hide_threshold, 1) or (
        listing.last_seen < stale_quarantine_cutoff
    )

    if should_hide and listing.is_active:
        listing.is_active = False

    db.commit()

    detail = (
        "Thanks. BagDrop hid this listing while the feed catches up."
        if should_hide
        else "Thanks. BagDrop logged the report and will watch this listing closely."
    )

    return ListingReportResponse(
        listing_id=listing.id,
        reason=reason,
        source=source,
        report_count_7d=report_count_7d,
        listing_hidden=bool(should_hide),
        detail=detail,
    )


@app.get("/api/admin/ops-summary", response_model=OpsSummaryResponse)
async def get_ops_summary(
    db: Session = Depends(get_db),
    _: None = Depends(_require_ops_access),
):
    """Minimal operations summary for scraper freshness, failures, and click activity."""
    now = datetime.utcnow()
    stale_after_hours = max(settings.scraper_interval_hours * 2, 6)
    stale_cutoff = now - timedelta(hours=stale_after_hours)
    click_cutoff = now - timedelta(hours=24)
    platforms: List[PlatformOpsResponse] = []
    digest_recipient_count = len(
        [item.strip() for item in settings.intelligence_digest_recipients.split(",") if item.strip()]
    )

    total_outbound_clicks_24h = (
        db.query(func.count(OutboundClick.id))
        .filter(OutboundClick.created_at >= click_cutoff)
        .scalar()
        or 0
    )
    active_watch_subscriptions = (
        db.query(func.count(WatchSubscription.id))
        .filter(WatchSubscription.is_active == True)
        .scalar()
        or 0
    )
    watch_alert_deliveries_24h = (
        db.query(func.count(WatchAlertDelivery.id))
        .filter(WatchAlertDelivery.created_at >= click_cutoff)
        .scalar()
        or 0
    )

    for platform in _platforms_to_monitor():
        latest_scrape = (
            db.query(Scrape)
            .filter(Scrape.platform == platform)
            .order_by(desc(Scrape.started_at))
            .first()
        )
        latest_success = (
            db.query(Scrape)
            .filter(and_(Scrape.platform == platform, Scrape.success == True))
            .order_by(desc(Scrape.completed_at), desc(Scrape.started_at))
            .first()
        )
        last_listing_sync_at = (
            db.query(func.max(Listing.last_seen))
            .filter(and_(Listing.platform == platform, Listing.is_active == True))
            .scalar()
        )
        active_listings = (
            db.query(func.count(Listing.id))
            .filter(and_(Listing.platform == platform, Listing.is_active == True))
            .scalar()
            or 0
        )
        outbound_clicks_24h = (
            db.query(func.count(OutboundClick.id))
            .filter(
                and_(
                    OutboundClick.platform == platform,
                    OutboundClick.created_at >= click_cutoff,
                )
            )
            .scalar()
            or 0
        )

        freshness_reference = None
        if latest_success and latest_success.completed_at:
            freshness_reference = latest_success.completed_at
        elif last_listing_sync_at:
            freshness_reference = last_listing_sync_at
        elif latest_scrape and latest_scrape.started_at:
            freshness_reference = latest_scrape.started_at

        stale = freshness_reference is None or freshness_reference < stale_cutoff

        platforms.append(
            PlatformOpsResponse(
                platform=platform,
                last_attempt_at=latest_scrape.started_at if latest_scrape else None,
                last_success_at=latest_success.completed_at if latest_success else None,
                last_listing_sync_at=last_listing_sync_at,
                last_run_success=latest_scrape.success if latest_scrape else None,
                stale=stale,
                error_message=latest_scrape.error_message if latest_scrape else None,
                listings_found=latest_scrape.listings_found if latest_scrape else None,
                active_listings=active_listings,
                outbound_clicks_24h=outbound_clicks_24h,
            )
        )

    return OpsSummaryResponse(
        generated_at=now,
        scrape_interval_hours=settings.scraper_interval_hours,
        stale_after_hours=stale_after_hours,
        total_outbound_clicks_24h=total_outbound_clicks_24h,
        active_watch_subscriptions=active_watch_subscriptions,
        watch_alert_deliveries_24h=watch_alert_deliveries_24h,
        smtp_configured=bool(settings.alert_from_email and settings.smtp_host),
        watch_alert_scheduler_enabled=settings.watch_alert_scheduler_enabled,
        intelligence_digest_enabled=settings.intelligence_digest_enabled,
        intelligence_digest_recipient_count=digest_recipient_count,
        platforms=platforms,
    )


@app.get("/api/admin/clicks/top", response_model=TopClicksResponse)
async def get_top_clicks(
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    _: None = Depends(_require_ops_access),
):
    """Top outbound-clicked listings and markets for monetization visibility."""
    return _build_top_clicks(db, days=days, limit=limit)


@app.post("/api/watchlists", response_model=WatchSubscriptionResponse, status_code=201)
async def subscribe_to_watchlist(
    payload: WatchSubscriptionRequest,
    db: Session = Depends(get_db),
):
    """Capture email-based watch intent for a brand/model market."""
    brand = (payload.brand or "").strip()
    model = (payload.model or "").strip()
    source = (payload.source or "unknown").strip() or "unknown"
    email = _normalize_watch_email(payload.email)

    if not brand or not model:
        raise HTTPException(status_code=400, detail="Brand and model are required")

    brand_slug = slugify_text(brand)
    model_slug = slugify_text(model)
    canonical_path = market_path(brand, model)

    existing = (
        db.query(WatchSubscription)
        .filter(
            and_(
                WatchSubscription.email == email,
                WatchSubscription.brand_slug == brand_slug,
                WatchSubscription.model_slug == model_slug,
            )
        )
        .first()
    )

    if existing:
        existing.brand = brand
        existing.model = model
        existing.source = source
        existing.is_active = True
        db.commit()
        db.refresh(existing)
        return WatchSubscriptionResponse(
            id=existing.id,
            email=existing.email,
            brand=existing.brand,
            model=existing.model,
            canonical_path=canonical_path,
            is_active=existing.is_active,
            already_subscribed=True,
            created_at=existing.created_at,
            unsubscribe_url=build_watch_unsubscribe_url(existing),
        )

    subscription = WatchSubscription(
        email=email,
        brand=brand,
        model=model,
        brand_slug=brand_slug,
        model_slug=model_slug,
        source=source,
        is_active=True,
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)

    return WatchSubscriptionResponse(
        id=subscription.id,
        email=subscription.email,
        brand=subscription.brand,
        model=subscription.model,
        canonical_path=canonical_path,
        is_active=subscription.is_active,
        already_subscribed=False,
        created_at=subscription.created_at,
        unsubscribe_url=build_watch_unsubscribe_url(subscription),
    )


@app.get("/api/watchlists/unsubscribe")
async def unsubscribe_watchlist(token: str, db: Session = Depends(get_db)):
    """Deactivate a watch subscription from an email-safe unsubscribe token."""
    subscription = resolve_watch_unsubscribe_token(token, db)
    if not subscription:
        raise HTTPException(status_code=400, detail="Invalid unsubscribe token")

    subscription.is_active = False
    db.commit()
    canonical_path = market_path(subscription.brand, subscription.model)
    redirect_url = f"{settings.public_app_url.rstrip('/')}{canonical_path}?watch=unsubscribed"
    return RedirectResponse(url=redirect_url, status_code=302)


@app.post("/api/admin/watchlists/send", response_model=WatchAlertRunResponse)
async def run_watchlist_alerts(
    dry_run: bool = Query(True),
    limit_subscriptions: Optional[int] = Query(None, ge=1, le=500),
    per_subscription_limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """Run the watchlist alert loop immediately."""
    try:
        return deliver_watch_alerts(
            db,
            dry_run=dry_run,
            limit_subscriptions=limit_subscriptions,
            per_subscription_limit=per_subscription_limit,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/admin/intelligence-digest/send", response_model=IntelligenceDigestRunResponse)
async def run_intelligence_digest(dry_run: bool = Query(True), db: Session = Depends(get_db)):
    """Run the intelligence digest delivery immediately."""
    from digest import send_intelligence_digest

    try:
        return send_intelligence_digest(db, dry_run=dry_run)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/admin/scrape")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    platform: Optional[str] = Query(None, description="Specific platform to scrape (or all if omitted)"),
    _: None = Depends(_require_ops_access),
):
    """Manually trigger a scrape run"""
    if platform:
        background_tasks.add_task(run_scraper, platform)
        return {"status": "scrape_started", "platform": platform}
    else:
        background_tasks.add_task(run_all_scrapers)
        return {"status": "scrape_started", "platform": "all"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.api_host, port=settings.api_port)
