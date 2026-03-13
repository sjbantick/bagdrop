"""Intelligence endpoints: stats, bag index, arbitrage, new drops, brief."""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from database import get_db
from deps import _public_listing_condition, _public_listing_cutoff, _require_ops_access, _round_float
from intelligence import compute_bag_index_rows, persist_bag_index_snapshots
from models import BagIndexSnapshot, Listing, PriceHistory
from schemas import (
    ArbitrageOpportunityResponse,
    BagIndexResponse,
    IntelligenceBriefResponse,
    ListingResponse,
    NewDropOpportunityResponse,
)
from utils import market_path

router = APIRouter()


# ---------------------------------------------------------------------------
# Query builders
# ---------------------------------------------------------------------------

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
        .join(market_stats, and_(
            Listing.brand == market_stats.c.brand,
            Listing.model == market_stats.c.model,
        ))
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

    opportunities = []
    for listing, market_listing_count, market_platform_count, market_average_price, market_lowest_price in rows:
        market_gap_amount = float(market_average_price) - float(listing.current_price)
        market_gap_pct = (market_gap_amount / float(market_average_price)) * 100 if market_average_price else 0
        opportunities.append(ArbitrageOpportunityResponse(
            listing=listing,
            canonical_path=market_path(listing.brand, listing.model),
            market_listing_count=int(market_listing_count),
            market_platform_count=int(market_platform_count),
            market_average_price=_round_float(market_average_price, 0) or 0,
            market_lowest_price=_round_float(market_lowest_price, 0) or 0,
            market_gap_amount=_round_float(market_gap_amount, 0) or 0,
            market_gap_pct=_round_float(market_gap_pct) or 0,
        ))
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
        .join(market_stats, and_(
            Listing.brand == market_stats.c.brand,
            Listing.model == market_stats.c.model,
        ))
        .filter(Listing.is_active == True, Listing.first_seen >= cutoff)
        .filter(Listing.last_seen >= _public_listing_cutoff())
        .order_by(desc(Listing.first_seen), desc(Listing.drop_pct))
        .all()
    )

    opportunities = []
    now = datetime.utcnow()
    for listing, market_average_price, market_platform_count in recent_listings:
        hours_since_first_seen = max((now - listing.first_seen).total_seconds() / 3600, 0.0)
        recency_score = max(0.0, 1 - (hours_since_first_seen / hours))
        drop_score = min((listing.drop_pct or 0) / 40, 1.0)
        market_gap_pct = 0.0
        if market_average_price and listing.current_price < market_average_price:
            market_gap_pct = (
                (float(market_average_price) - float(listing.current_price))
                / float(market_average_price)
            ) * 100
        gap_score = min(max(market_gap_pct, 0.0) / 25, 1.0)
        platform_score = min(max((int(market_platform_count or 1) - 1) / 3, 0.0), 1.0)
        significance_score = round(
            (drop_score * 40 + recency_score * 35 + gap_score * 15 + platform_score * 10) * 100 / 100, 1
        )

        if significance_score < min_significance:
            continue

        opportunities.append(NewDropOpportunityResponse(
            listing=listing,
            canonical_path=market_path(listing.brand, listing.model),
            hours_since_first_seen=round(hours_since_first_seen, 1),
            significance_score=significance_score,
            market_gap_pct=_round_float(market_gap_pct) or 0,
            market_platform_count=int(market_platform_count or 1),
        ))

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
        key=lambda row: (0 if row.delta_pct is None else abs(row.delta_pct), row.active_listings_count),
        reverse=True,
    )[:bag_index_limit]

    return IntelligenceBriefResponse(
        generated_at=datetime.utcnow(),
        arbitrage=_build_arbitrage_opportunities(db, limit=arbitrage_limit, min_market_listings=3, min_platforms=2, min_gap_pct=12),
        new_drops=_build_new_drop_opportunities(db, hours=72, limit=new_drop_limit, min_significance=35),
        bag_index_movers=[BagIndexResponse(**row.__dict__) for row in ranked_bag_index],
    )


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get overall stats for the header display."""
    avg_drop = db.query(func.avg(Listing.drop_pct)).filter(
        _public_listing_condition(Listing.drop_pct > 0)
    ).scalar()
    total_active = db.query(func.count(Listing.id)).filter(_public_listing_condition()).scalar() or 0
    biggest_drop = db.query(func.max(Listing.drop_pct)).filter(_public_listing_condition()).scalar()
    # Drops today: listings whose price history has an entry in the last 24h
    drops_today = (
        db.query(func.count(func.distinct(PriceHistory.listing_id)))
        .filter(PriceHistory.detected_at >= datetime.utcnow() - timedelta(hours=24))
        .scalar()
        or 0
    )
    return {
        "total_active_listings": total_active,
        "avg_drop_pct": round(float(avg_drop), 1) if avg_drop else None,
        "biggest_drop_pct": round(float(biggest_drop), 1) if biggest_drop else None,
        "drops_today": drops_today,
    }


@router.get("/api/bag-index", response_model=List[BagIndexResponse])
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


@router.post("/api/admin/bag-index/recompute", response_model=List[BagIndexResponse])
async def recompute_bag_index(
    limit: int = Query(20, ge=1, le=100),
    min_active_listings: int = Query(2, ge=1, le=20),
    persist: bool = Query(True),
    db: Session = Depends(get_db),
    _: None = Depends(_require_ops_access),
):
    """Recompute current brand-level BagIndex values and optionally persist snapshots."""
    rows = (
        persist_bag_index_snapshots(db, limit=limit, min_active_listings=min_active_listings)
        if persist
        else compute_bag_index_rows(db, limit=limit, min_active_listings=min_active_listings)
    )
    return [BagIndexResponse(**row.__dict__) for row in rows]


@router.get("/api/intelligence/brief", response_model=IntelligenceBriefResponse)
async def get_intelligence_brief(db: Session = Depends(get_db)):
    """Combined daily intelligence payload for owned BagDrop editorial surfaces."""
    return _build_intelligence_brief(db)


@router.get("/api/opportunities/arbitrage", response_model=List[ArbitrageOpportunityResponse])
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


@router.get("/api/opportunities/new-drops", response_model=List[NewDropOpportunityResponse])
async def get_new_drop_opportunities(
    hours: int = Query(72, ge=6, le=168),
    limit: int = Query(12, ge=1, le=48),
    min_significance: float = Query(35.0, ge=5.0, le=95.0),
    db: Session = Depends(get_db),
):
    """High-signal new drops ranked by freshness, markdown, and market context."""
    return _build_new_drop_opportunities(db, hours=hours, limit=limit, min_significance=min_significance)
