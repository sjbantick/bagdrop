"""Shared FastAPI dependencies and utility functions for BagDrop routes."""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import Header, HTTPException, Query
from sqlalchemy import and_
from sqlalchemy.orm import Session

from config import settings
from models import Listing, OutboundClick


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


def _require_ops_access(
    token: Optional[str] = Query(None),
    x_ops_token: Optional[str] = Header(None, alias="x-ops-token"),
):
    expected = (settings.ops_dashboard_token or "").strip()
    if not expected:
        raise HTTPException(status_code=404, detail="Not found")
    actual = (token or x_ops_token or "").strip()
    if actual != expected:
        raise HTTPException(status_code=404, detail="Not found")


def _extract_client_ip(request) -> Optional[str]:
    if not request:
        return None
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        first = forwarded.split(",")[0].strip()
        if first:
            return first
    for header in ["cf-connecting-ip", "x-real-ip"]:
        value = (request.headers.get(header) or "").strip()
        if value:
            return value
    return getattr(getattr(request, "client", None), "host", None)


def _normalize_ip_list(values: Optional[str]) -> List[str]:
    if not values:
        return []
    return [item.strip() for item in values.split(",") if item.strip()]


def _apply_outbound_ip_exclusion(query, excluded_ips: List[str]):
    if not excluded_ips:
        return query
    return query.filter(~OutboundClick.client_ip.in_(excluded_ips))
