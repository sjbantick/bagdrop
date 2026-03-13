"""Admin and ops endpoints: summary, top clicks, scrape trigger, normalisation."""
import re
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session

from config import settings
from database import get_db
from deps import (
    _apply_outbound_ip_exclusion,
    _normalize_ip_list,
    _require_ops_access,
    _round_float,
)
from models import (
    BagIndexSnapshot,
    Listing,
    OutboundClick,
    Platform,
    Scrape,
    WatchAlertDelivery,
    WatchSubscription,
)
from scheduler import run_all_scrapers, run_scraper
from schemas import (
    AdminHydrationResponse,
    OpsSummaryResponse,
    PlatformOpsResponse,
    TopClickContextResponse,
    TopClickedListingResponse,
    TopClickedMarketResponse,
    TopClickPlatformResponse,
    TopClicksResponse,
    TopClickSurfaceResponse,
)
from utils import market_path

router = APIRouter()


def _platforms_to_monitor() -> List[str]:
    enabled_platforms = [
        (Platform.FASHIONPHILE, settings.enable_fashionphile),
        (Platform.REALREAL, settings.enable_realreal),
        (Platform.REBAG, settings.enable_rebag),
        (Platform.VESTIAIRE, settings.enable_vestiaire),
        (Platform.YOOGI, settings.enable_yoogi),
        (Platform.COSETTE, settings.enable_cosette),
        (Platform.THE_PURSE_AFFAIR, settings.enable_thepurseaffair),
        (Platform.LUXEDH, settings.enable_luxedh),
        (Platform.MADISON_AVENUE_COUTURE, settings.enable_madisonavenuecouture),
    ]
    return [platform.value for platform, enabled in enabled_platforms if enabled]


def _build_top_clicks(
    db: Session,
    *,
    days: int = 7,
    limit: int = 10,
    excluded_ips: Optional[List[str]] = None,
) -> TopClicksResponse:
    cutoff = datetime.utcnow() - timedelta(days=days)
    excluded_ips = excluded_ips or []

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
        .filter(~OutboundClick.client_ip.in_(excluded_ips) if excluded_ips else True)
        .group_by(OutboundClick.listing_id, Listing.brand, Listing.model, Listing.platform, Listing.current_price)
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
        .filter(~OutboundClick.client_ip.in_(excluded_ips) if excluded_ips else True)
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
        .filter(~OutboundClick.client_ip.in_(excluded_ips) if excluded_ips else True)
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
        .filter(~OutboundClick.client_ip.in_(excluded_ips) if excluded_ips else True)
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
        .filter(and_(
            OutboundClick.created_at >= cutoff,
            OutboundClick.context.isnot(None),
            OutboundClick.context != "",
        ))
        .filter(~OutboundClick.client_ip.in_(excluded_ips) if excluded_ips else True)
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


async def get_ops_summary(db: Session, *, exclude_ips: Optional[List[str]] = None) -> OpsSummaryResponse:
    """Compute operations summary for scraper freshness, failures, and click activity."""
    now = datetime.utcnow()
    stale_after_hours = max(settings.scraper_interval_hours * 2, 6)
    stale_cutoff = now - timedelta(hours=stale_after_hours)
    click_cutoff = now - timedelta(hours=24)
    excluded_ips = exclude_ips or []
    platforms: List[PlatformOpsResponse] = []

    digest_recipient_count = len(
        [item.strip() for item in settings.intelligence_digest_recipients.split(",") if item.strip()]
    )

    total_clicks_query = db.query(func.count(OutboundClick.id)).filter(OutboundClick.created_at >= click_cutoff)
    total_outbound_clicks_24h = _apply_outbound_ip_exclusion(total_clicks_query, excluded_ips).scalar() or 0
    active_watch_subscriptions = (
        db.query(func.count(WatchSubscription.id)).filter(WatchSubscription.is_active == True).scalar() or 0
    )
    watch_alert_deliveries_24h = (
        db.query(func.count(WatchAlertDelivery.id)).filter(WatchAlertDelivery.created_at >= click_cutoff).scalar() or 0
    )

    for platform in _platforms_to_monitor():
        latest_scrape = (
            db.query(Scrape).filter(Scrape.platform == platform).order_by(desc(Scrape.started_at)).first()
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
        platform_clicks_query = db.query(func.count(OutboundClick.id)).filter(and_(
            OutboundClick.platform == platform,
            OutboundClick.created_at >= click_cutoff,
        ))
        outbound_clicks_24h = _apply_outbound_ip_exclusion(platform_clicks_query, excluded_ips).scalar() or 0

        freshness_reference = None
        if latest_success and latest_success.completed_at:
            freshness_reference = latest_success.completed_at
        elif last_listing_sync_at:
            freshness_reference = last_listing_sync_at
        elif latest_scrape and latest_scrape.started_at:
            freshness_reference = latest_scrape.started_at

        stale = freshness_reference is None or freshness_reference < stale_cutoff

        platforms.append(PlatformOpsResponse(
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
        ))

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


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/api/admin/ops-summary", response_model=OpsSummaryResponse)
async def get_ops_summary_route(
    request: Request,
    db: Session = Depends(get_db),
    _: None = Depends(_require_ops_access),
):
    exclude_ips = _normalize_ip_list(request.query_params.get("exclude_ips"))
    return await get_ops_summary(db, exclude_ips=exclude_ips)


@router.get("/api/admin/clicks/top", response_model=TopClicksResponse)
async def get_top_clicks_route(
    request: Request,
    days: int = Query(7, ge=1, le=90),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    _: None = Depends(_require_ops_access),
):
    """Top outbound-clicked listings and markets for monetization visibility."""
    excluded_ips = _normalize_ip_list(request.query_params.get("exclude_ips"))
    return _build_top_clicks(db, days=days, limit=limit, excluded_ips=excluded_ips)


@router.post("/api/admin/scrape")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    platform: Optional[str] = Query(None, description="Specific platform to scrape (or all if omitted)"),
    _: None = Depends(_require_ops_access),
):
    """Manually trigger a scrape run."""
    if platform:
        background_tasks.add_task(run_scraper, platform)
        return {"status": "scrape_started", "platform": platform}
    background_tasks.add_task(run_all_scrapers)
    return {"status": "scrape_started", "platform": "all"}


@router.post("/api/admin/rebag/hydrate", response_model=AdminHydrationResponse)
async def hydrate_rebag_handles(
    handles: str = Query(..., min_length=1, description="Comma or newline separated Rebag product handles"),
    _: None = Depends(_require_ops_access),
    db: Session = Depends(get_db),
):
    from scrapers.rebag import RebagScraper

    requested_handles = [handle.strip() for handle in re.split(r"[\n,]", handles) if handle.strip()]
    if not requested_handles:
        raise HTTPException(status_code=400, detail="No valid Rebag handles provided")

    scraper = RebagScraper(db)
    try:
        found, new, updated = await scraper.hydrate_handles(requested_handles)
    finally:
        await scraper.close()

    return AdminHydrationResponse(
        platform="rebag",
        requested_handles=len(requested_handles),
        listings_found=found,
        listings_new=new,
        listings_updated=updated,
    )


@router.post("/api/admin/normalize-brands")
async def normalize_brands_route(
    _: None = Depends(_require_ops_access),
    db: Session = Depends(get_db),
):
    """Fix brand name casing in place for all existing listings and bag-index snapshots."""
    from scrapers.base import BaseScraper

    class _Norm(BaseScraper):
        platform = None
        base_url = ""
        async def scrape(self, db): pass

    norm = _Norm.__new__(_Norm)

    listings = db.query(Listing).all()
    listing_updates = 0
    for listing in listings:
        fixed = norm.normalize_brand(listing.brand or "")
        if fixed != listing.brand:
            listing.brand = fixed
            listing_updates += 1

    snapshots = db.query(BagIndexSnapshot).all()
    snapshot_updates = 0
    for snap in snapshots:
        fixed = norm.normalize_brand(snap.brand or "")
        if fixed != snap.brand:
            snap.brand = fixed
            snapshot_updates += 1

    db.commit()
    return {
        "listings_updated": listing_updates,
        "snapshots_updated": snapshot_updates,
        "total_listings": len(listings),
    }
