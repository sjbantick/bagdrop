"""Watchlist subscribe/unsubscribe and admin alert delivery routes."""
import re
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from sqlalchemy import and_
from sqlalchemy.orm import Session

from alerts import build_watch_unsubscribe_url, deliver_watch_alerts, resolve_watch_unsubscribe_token
from config import settings
from database import get_db
from deps import _require_ops_access
from models import WatchSubscription
from schemas import (
    IntelligenceDigestRunResponse,
    WatchAlertRunResponse,
    WatchSubscriptionRequest,
    WatchSubscriptionResponse,
)
from utils import market_path, slugify_text

router = APIRouter()


def _normalize_watch_email(email: str) -> str:
    normalized = (email or "").strip().lower()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", normalized):
        raise HTTPException(status_code=400, detail="A valid email address is required")
    return normalized


@router.post("/api/watchlists", response_model=WatchSubscriptionResponse, status_code=201)
async def subscribe_to_watchlist(
    payload: WatchSubscriptionRequest,
    db: Session = Depends(get_db),
):
    """Capture email-based watch intent for a brand/model market."""
    brand = (payload.brand or "").strip()
    model = (payload.model or "").strip()
    source = (payload.source or "unknown").strip() or "unknown"
    target_price = payload.target_price
    email = _normalize_watch_email(payload.email)

    if not brand or not model:
        raise HTTPException(status_code=400, detail="Brand and model are required")

    brand_slug = slugify_text(brand)
    model_slug = slugify_text(model)
    canonical_path = market_path(brand, model)

    existing = (
        db.query(WatchSubscription)
        .filter(and_(
            WatchSubscription.email == email,
            WatchSubscription.brand_slug == brand_slug,
            WatchSubscription.model_slug == model_slug,
        ))
        .first()
    )

    if existing:
        existing.brand = brand
        existing.model = model
        existing.source = source
        existing.target_price = target_price
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
            target_price=existing.target_price,
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
        target_price=target_price,
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
        target_price=subscription.target_price,
        created_at=subscription.created_at,
        unsubscribe_url=build_watch_unsubscribe_url(subscription),
    )


@router.get("/api/watchlists/unsubscribe")
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


@router.post("/api/admin/watchlists/send", response_model=WatchAlertRunResponse)
async def run_watchlist_alerts(
    dry_run: bool = Query(True),
    limit_subscriptions: Optional[int] = Query(None, ge=1, le=500),
    per_subscription_limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db),
    _: None = Depends(_require_ops_access),
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


@router.post("/api/admin/intelligence-digest/send", response_model=IntelligenceDigestRunResponse)
async def run_intelligence_digest(
    dry_run: bool = Query(True),
    db: Session = Depends(get_db),
    _: None = Depends(_require_ops_access),
):
    """Run the intelligence digest delivery immediately."""
    from digest import send_intelligence_digest

    try:
        return send_intelligence_digest(db, dry_run=dry_run)
    except RuntimeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
