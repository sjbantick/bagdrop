"""Listing feed, detail, outbound click tracking, and brand/model routes."""
import base64
import json
import re
from datetime import datetime, timedelta
from typing import List, Optional
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit, quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from cache import cache_get, cache_set
from config import settings
from database import get_db
from deps import _extract_client_ip, _public_listing_condition, _public_listing_cutoff
from models import Listing, ListingReport, OutboundClick, PriceHistory
from schemas import (
    ListingReportRequest,
    ListingReportResponse,
    ListingResponse,
    PaginatedListingsResponse,
    PriceHistoryResponse,
)
from utils import slugify_text

router = APIRouter()


# ---------------------------------------------------------------------------
# Affiliate URL helpers
# ---------------------------------------------------------------------------

def _render_affiliate_template(value: str, replacements: Optional[dict] = None) -> str:
    if not replacements:
        return value

    def replace(match: re.Match) -> str:
        return str(replacements.get(match.group(1), ""))

    return re.sub(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", replace, value)


def _affiliate_url_template_for_platform(platform: str) -> str:
    return {
        "realreal": settings.realreal_affiliate_url_template,
        "vestiaire": settings.vestiaire_affiliate_url_template,
        "fashionphile": settings.fashionphile_affiliate_url_template,
        "rebag": settings.rebag_affiliate_url_template,
    }.get(platform, "")


def _affiliate_query_for_platform(
    platform: str,
    replacements: Optional[dict] = None,
) -> dict:
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

    destination = urlunsplit((
        split.scheme,
        split.netloc,
        split.path,
        urlencode(query, doseq=True),
        split.fragment,
    ))

    # If a full redirect-URL template is configured for this platform, wrap the
    # destination URL inside it (e.g. ShareASale, Rakuten, CJ, Impact deep links).
    url_template = _affiliate_url_template_for_platform(listing.platform)
    if url_template:
        return url_template.replace("{{url}}", quote(destination, safe=""))

    return destination


# ---------------------------------------------------------------------------
# Report helpers
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Cursor helpers
# ---------------------------------------------------------------------------

def _encode_cursor(sort_by: str, sort_value, listing_id: str) -> str:
    data = {"s": sort_by, "v": str(sort_value) if sort_value is not None else None, "id": listing_id}
    return base64.urlsafe_b64encode(json.dumps(data, separators=(",", ":")).encode()).decode()


def _decode_cursor(cursor: str) -> Optional[dict]:
    try:
        return json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/api/listings", response_model=PaginatedListingsResponse)
async def get_listings(
    db: Session = Depends(get_db),
    brand: Optional[str] = Query(None),
    model: Optional[str] = Query(None),
    platform: Optional[str] = Query(None),
    min_drop_pct: Optional[float] = Query(0),
    max_drop_pct: Optional[float] = Query(100),
    sort_by: str = Query("drop_pct", pattern="^(drop_pct|drop_amount|current_price|last_seen)$"),
    limit: int = Query(60, le=500),
    cursor: Optional[str] = Query(None),
):
    """Get listings with optional filters. Sorted by biggest drop by default.
    Cursor-based pagination: pass `cursor` from previous response's `next_cursor`.
    """
    col_map = {
        "drop_pct": Listing.drop_pct,
        "drop_amount": Listing.drop_amount,
        "current_price": Listing.current_price,
        "last_seen": Listing.last_seen,
    }
    sort_col = col_map[sort_by]

    query = db.query(Listing).filter(Listing.is_active == True)
    query = query.filter(Listing.last_seen >= _public_listing_cutoff())

    if brand:
        query = query.filter(Listing.brand.ilike(f"%{brand}%"))
    if model:
        query = query.filter(Listing.model.ilike(f"%{model}%"))
    if platform:
        query = query.filter(Listing.platform == platform)
    if min_drop_pct is not None:
        query = query.filter(Listing.drop_pct >= min_drop_pct)
    if max_drop_pct is not None:
        query = query.filter(Listing.drop_pct <= max_drop_pct)

    # Apply keyset cursor: skip rows already seen based on (sort_col, id) tiebreak
    cursor_data = _decode_cursor(cursor) if cursor else None
    if cursor_data and cursor_data.get("s") == sort_by and cursor_data.get("v") is not None:
        cursor_v = cursor_data["v"]
        cursor_id = cursor_data["id"]
        if sort_by == "last_seen":
            from datetime import timezone
            # last_seen cursor value is stored as ISO string
            try:
                cursor_dt = datetime.fromisoformat(cursor_v)
            except ValueError:
                cursor_dt = None
            if cursor_dt:
                query = query.filter(
                    or_(sort_col < cursor_dt, and_(sort_col == cursor_dt, Listing.id < cursor_id))
                )
        else:
            cursor_float = float(cursor_v)
            query = query.filter(
                or_(sort_col < cursor_float, and_(sort_col == cursor_float, Listing.id < cursor_id))
            )

    query = query.order_by(desc(sort_col), desc(Listing.id))

    # Fetch one extra to detect has_more without a separate COUNT query
    rows = query.limit(limit + 1).all()
    has_more = len(rows) > limit
    items = rows[:limit]

    next_cursor = None
    if has_more and items:
        last = items[-1]
        sort_val = getattr(last, sort_by)
        if sort_by == "last_seen" and sort_val is not None:
            sort_val = sort_val.isoformat()
        next_cursor = _encode_cursor(sort_by, sort_val, last.id)

    return PaginatedListingsResponse(items=items, next_cursor=next_cursor, has_more=has_more)


@router.get("/api/listings/{listing_id}", response_model=ListingResponse)
async def get_listing(listing_id: str, db: Session = Depends(get_db)):
    """Get a specific listing."""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
        raise HTTPException(status_code=404, detail="Listing not found")
    if not listing.is_active or listing.last_seen < _public_listing_cutoff():
        if listing.is_active:
            listing.is_active = False
            db.commit()
        raise HTTPException(status_code=404, detail="Listing not found")
    return listing


@router.get("/api/listings/{listing_id}/price-history", response_model=List[PriceHistoryResponse])
async def get_listing_price_history(listing_id: str, db: Session = Depends(get_db)):
    """Get price history for a listing."""
    return (
        db.query(PriceHistory)
        .filter(PriceHistory.listing_id == listing_id)
        .order_by(PriceHistory.detected_at)
        .all()
    )


@router.get("/api/listings/{listing_id}/outbound")
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
        client_ip=_extract_client_ip(request),
    )
    db.add(click)
    db.commit()

    return RedirectResponse(url=target_url, status_code=307)


@router.post("/api/listings/{listing_id}/report", response_model=ListingReportResponse)
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

    now = datetime.utcnow()
    reason = _normalize_listing_report_reason(payload.reason)
    source = (payload.source or "unknown").strip()[:100] or "unknown"
    notes = _normalize_listing_report_notes(payload.notes)
    reporter_ip = _extract_client_ip(request)
    user_agent = request.headers.get("user-agent")

    if reporter_ip:
        daily_limit_cutoff = now - timedelta(hours=24)
        daily_ip_reports = (
            db.query(func.count(ListingReport.id))
            .filter(
                and_(
                    ListingReport.reporter_ip == reporter_ip,
                    ListingReport.created_at >= daily_limit_cutoff,
                )
            )
            .scalar()
            or 0
        )
        if daily_ip_reports >= max(settings.listing_report_ip_daily_limit, 1):
            raise HTTPException(status_code=429, detail="Too many listing reports from this IP")

    dedupe_cutoff = now - timedelta(hours=max(settings.listing_report_dedupe_hours, 1))
    duplicate_matchers = []
    if reporter_ip:
        duplicate_matchers.append(ListingReport.reporter_ip == reporter_ip)
    if user_agent:
        duplicate_matchers.append(ListingReport.user_agent == user_agent)

    recent_duplicate = None
    if duplicate_matchers:
        recent_duplicate = (
            db.query(ListingReport)
            .filter(
                and_(
                    ListingReport.listing_id == listing.id,
                    ListingReport.reason == reason,
                    ListingReport.created_at >= dedupe_cutoff,
                    or_(*duplicate_matchers),
                )
            )
            .order_by(desc(ListingReport.created_at))
            .first()
        )

    if not recent_duplicate:
        report = ListingReport(
            listing_id=listing.id,
            platform=listing.platform,
            reason=reason,
            source=source,
            notes=notes,
            reporter_ip=reporter_ip,
            user_agent=user_agent,
        )
        db.add(report)
        db.flush()

    report_cutoff = now - timedelta(days=7)
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

    stale_quarantine_cutoff = now - timedelta(
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
        else (
            "Thanks. BagDrop already logged this report recently and will keep watching the listing."
            if recent_duplicate
            else "Thanks. BagDrop logged the report and will watch this listing closely."
        )
    )

    return ListingReportResponse(
        listing_id=listing.id,
        reason=reason,
        source=source,
        report_count_7d=report_count_7d,
        listing_hidden=bool(should_hide),
        detail=detail,
    )


@router.get("/api/brands")
async def get_brands(db: Session = Depends(get_db)):
    """Get all unique brands."""
    cache_key = "bagdrop:v1:brands"
    cached = await cache_get(cache_key)
    if cached:
        return cached
    brands = (
        db.query(Listing.brand)
        .filter(_public_listing_condition())
        .distinct()
        .order_by(Listing.brand)
        .all()
    )
    result = [b[0] for b in brands]
    await cache_set(cache_key, result, ttl=900)  # 15 min — brands change rarely
    return result


@router.get("/api/brands/{brand}/models")
async def get_models_for_brand(brand: str, db: Session = Depends(get_db)):
    """Get all models for a brand."""
    models = (
        db.query(Listing.model)
        .filter(_public_listing_condition(Listing.brand.ilike(brand)))
        .distinct()
        .order_by(Listing.model)
        .all()
    )
    return [m[0] for m in models]


@router.get("/api/new-drops", response_model=List[ListingResponse])
async def get_new_drops(
    hours: int = Query(24, ge=1, le=168),
    limit: int = Query(50, le=500),
    db: Session = Depends(get_db),
):
    """Get new drops in the last N hours (detected_at in price_history)."""
    time_cutoff = datetime.utcnow() - timedelta(hours=hours)
    recent_listing_ids = (
        db.query(PriceHistory.listing_id)
        .filter(PriceHistory.detected_at >= time_cutoff)
        .distinct()
        .all()
    )
    listing_ids = [lid[0] for lid in recent_listing_ids]
    if not listing_ids:
        return []
    return (
        db.query(Listing)
        .filter(_public_listing_condition(Listing.id.in_(listing_ids)))
        .order_by(desc(Listing.drop_pct))
        .limit(limit)
        .all()
    )
