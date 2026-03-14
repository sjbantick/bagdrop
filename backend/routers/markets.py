"""Canonical brand/model market pages and velocity scoring."""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from cache import cache_get, cache_set
from database import get_db
from deps import _public_listing_condition, _public_listing_cutoff, _round_float
from models import Listing, PriceHistory
from schemas import (
    FeaturedMarketResponse,
    MarketResponse,
    MarketStatsResponse,
    MarketVelocityResponse,
    PlatformBreakdownResponse,
    PriceTrendResponse,
    PriceTrendPointResponse,
    ListingResponse,
)
from utils import market_path, slugify_text

router = APIRouter()


def _velocity_label(score: float) -> str:
    if score >= 75:
        return "hot"
    if score >= 45:
        return "active"
    if score >= 20:
        return "stable"
    return "slow"


def _resolve_market(db: Session, brand_slug: str, model_slug: str) -> Optional[tuple]:
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


def _build_market_velocity(db: Session, brand: str, model: str) -> MarketVelocityResponse:
    now = datetime.utcnow()
    windows = {
        "7d": now - timedelta(days=7),
        "30d": now - timedelta(days=30),
        "60d": now - timedelta(days=60),
        "90d": now - timedelta(days=90),
    }

    base_query = db.query(Listing).filter(
        _public_listing_condition(Listing.brand == brand, Listing.model == model)
    )
    active_listings = base_query.count()
    platform_count = (
        db.query(func.count(func.distinct(Listing.platform)))
        .filter(and_(Listing.is_active == True, Listing.brand == brand, Listing.model == model))
        .scalar()
        or 0
    )

    recent_counts = {}
    for label, cutoff in windows.items():
        recent_counts[label] = (
            db.query(func.count(Listing.id))
            .filter(and_(
                Listing.is_active == True,
                Listing.brand == brand,
                Listing.model == model,
                Listing.first_seen >= cutoff,
            ))
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


@router.get("/api/markets/featured", response_model=List[FeaturedMarketResponse])
async def get_featured_markets(
    limit: int = Query(12, ge=1, le=48),
    min_listings: int = Query(2, ge=1, le=50),
    db: Session = Depends(get_db),
):
    """Get high-signal brand/model markets to surface on the homepage."""
    cache_key = f"bagdrop:v1:markets-featured:{limit}:{min_listings}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

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

    result = [
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
    await cache_set(cache_key, [r.model_dump() for r in result], ttl=300)
    return result


@router.get("/api/markets/{brand_slug}/{model_slug}/velocity", response_model=MarketVelocityResponse)
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


@router.get("/api/markets/{brand_slug}/{model_slug}/price-trend", response_model=PriceTrendResponse)
async def get_market_price_trend(
    brand_slug: str,
    model_slug: str,
    db: Session = Depends(get_db),
):
    """Weekly aggregated price trend for a brand/model market (last 90 days)."""
    cache_key = f"bagdrop:v1:price-trend:{brand_slug}:{model_slug}"
    cached = await cache_get(cache_key)
    if cached:
        return cached

    resolved = _resolve_market(db, brand_slug, model_slug)
    if not resolved:
        raise HTTPException(status_code=404, detail="Market not found")
    brand, model = resolved

    cutoff = datetime.utcnow() - timedelta(days=90)

    week_start_expr = func.date_trunc("week", PriceHistory.detected_at)

    rows = (
        db.query(
            week_start_expr.label("week_start"),
            func.avg(PriceHistory.price).label("avg_price"),
            func.min(PriceHistory.price).label("min_price"),
            func.max(PriceHistory.price).label("max_price"),
            func.count(PriceHistory.id).label("data_points"),
        )
        .join(Listing, Listing.id == PriceHistory.listing_id)
        .filter(
            and_(
                Listing.brand == brand,
                Listing.model == model,
                PriceHistory.detected_at >= cutoff,
            )
        )
        .group_by(week_start_expr)
        .order_by(week_start_expr)
        .all()
    )

    trend_points = [
        PriceTrendPointResponse(
            week_start=row.week_start.strftime("%Y-%m-%d"),
            avg_price=_round_float(row.avg_price, 0),
            min_price=_round_float(row.min_price, 0),
            max_price=_round_float(row.max_price, 0),
            data_points=row.data_points,
        )
        for row in rows
    ]

    data_points_total = sum(p.data_points for p in trend_points)

    # Determine trend direction: compare avg of most recent 2 weeks vs prior 2 weeks
    trend_direction = "stable"
    trend_pct: Optional[float] = None
    if len(trend_points) >= 4:
        recent_avg = (trend_points[-1].avg_price + trend_points[-2].avg_price) / 2
        prior_avg = (trend_points[-3].avg_price + trend_points[-4].avg_price) / 2
        if prior_avg > 0:
            trend_pct = _round_float(((recent_avg - prior_avg) / prior_avg) * 100)
            if trend_pct <= -2:
                trend_direction = "declining"
            elif trend_pct >= 2:
                trend_direction = "rising"
    elif len(trend_points) >= 2:
        recent_avg = trend_points[-1].avg_price
        prior_avg = trend_points[0].avg_price
        if prior_avg > 0:
            trend_pct = _round_float(((recent_avg - prior_avg) / prior_avg) * 100)
            if trend_pct <= -2:
                trend_direction = "declining"
            elif trend_pct >= 2:
                trend_direction = "rising"

    result = PriceTrendResponse(
        brand=brand,
        model=model,
        canonical_path=market_path(brand, model),
        trend_direction=trend_direction,
        trend_pct=trend_pct,
        data_points_total=data_points_total,
        trend=[p.model_dump() for p in trend_points],
    )
    await cache_set(cache_key, result.model_dump(), ttl=600)
    return result


@router.get("/api/markets/{brand_slug}/{model_slug}", response_model=MarketResponse)
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
        _public_listing_condition(Listing.brand == brand, Listing.model == model)
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
        .filter(_public_listing_condition(Listing.brand == brand, Listing.model == model))
        .one()
    )

    platform_listing_count = func.count(Listing.id)
    platform_rows = (
        db.query(
            Listing.platform.label("platform"),
            platform_listing_count.label("listing_count"),
        )
        .filter(_public_listing_condition(Listing.brand == brand, Listing.model == model))
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
            PlatformBreakdownResponse(platform=row.platform, listing_count=row.listing_count)
            for row in platform_rows
        ],
        listings=listings,
    )
