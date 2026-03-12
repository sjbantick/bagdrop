"""Reusable market intelligence helpers for BagDrop."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional

from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from models import BagIndexSnapshot, Listing


@dataclass
class BagIndexRow:
    brand: str
    index_value: float
    snapshot_date: datetime
    current_avg_price: Optional[float]
    active_listings_count: int
    peak_avg_price: Optional[float]
    avg_drop_pct: Optional[float]
    previous_index_value: Optional[float]
    delta_pct: Optional[float]
    trend: str


def _round_float(value: Optional[float], digits: int = 1) -> Optional[float]:
    if value is None:
        return None
    rounded = round(float(value), digits)
    if rounded == 0:
        return 0.0
    return rounded


def _trend_label(delta_pct: Optional[float]) -> str:
    if delta_pct is None:
        return "new"
    if delta_pct >= 1:
        return "up"
    if delta_pct <= -1:
        return "down"
    return "flat"


def compute_bag_index_rows(
    db: Session,
    *,
    limit: int = 20,
    min_active_listings: int = 2,
    snapshot_time: Optional[datetime] = None,
) -> List[BagIndexRow]:
    rows = (
        db.query(
            Listing.brand.label("brand"),
            func.avg(Listing.current_price).label("current_avg_price"),
            func.count(Listing.id).label("active_listings_count"),
            func.avg(Listing.drop_pct).label("avg_drop_pct"),
        )
        .filter(Listing.is_active == True)
        .group_by(Listing.brand)
        .having(func.count(Listing.id) >= min_active_listings)
        .order_by(func.count(Listing.id).desc(), Listing.brand)
        .limit(limit)
        .all()
    )

    snapshot_time = snapshot_time or datetime.utcnow()
    results: List[BagIndexRow] = []

    for row in rows:
        latest_snapshot = (
            db.query(BagIndexSnapshot)
            .filter(BagIndexSnapshot.brand == row.brand)
            .order_by(BagIndexSnapshot.snapshot_date.desc())
            .first()
        )
        previous_peak = (
            db.query(func.max(BagIndexSnapshot.peak_avg_price))
            .filter(BagIndexSnapshot.brand == row.brand)
            .scalar()
        )

        current_avg_price = float(row.current_avg_price) if row.current_avg_price is not None else 0.0
        peak_avg_price = max(float(previous_peak or 0), current_avg_price)
        index_value = (current_avg_price / peak_avg_price * 100) if peak_avg_price else 100.0
        previous_index_value = float(latest_snapshot.index_value) if latest_snapshot else None
        delta_pct = (
            _round_float(index_value - previous_index_value, 1)
            if previous_index_value is not None
            else None
        )

        results.append(
            BagIndexRow(
                brand=row.brand,
                index_value=round(index_value, 1),
                snapshot_date=snapshot_time,
                peak_avg_price=round(peak_avg_price, 0) if peak_avg_price else None,
                current_avg_price=round(current_avg_price, 0) if current_avg_price else None,
                active_listings_count=int(row.active_listings_count or 0),
                avg_drop_pct=_round_float(row.avg_drop_pct),
                previous_index_value=round(previous_index_value, 1) if previous_index_value is not None else None,
                delta_pct=delta_pct,
                trend=_trend_label(delta_pct),
            )
        )

    return results


def persist_bag_index_snapshots(
    db: Session,
    *,
    limit: int = 20,
    min_active_listings: int = 2,
    snapshot_time: Optional[datetime] = None,
) -> List[BagIndexRow]:
    snapshot_time = snapshot_time or datetime.utcnow()
    start_of_day = snapshot_time.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = start_of_day + timedelta(days=1)
    rows = compute_bag_index_rows(
        db,
        limit=limit,
        min_active_listings=min_active_listings,
        snapshot_time=snapshot_time,
    )

    for row in rows:
        existing = (
            db.query(BagIndexSnapshot)
            .filter(
                and_(
                    BagIndexSnapshot.brand == row.brand,
                    BagIndexSnapshot.snapshot_date >= start_of_day,
                    BagIndexSnapshot.snapshot_date < end_of_day,
                )
            )
            .order_by(BagIndexSnapshot.snapshot_date.desc())
            .first()
        )

        if existing:
            existing.snapshot_date = row.snapshot_date
            existing.index_value = row.index_value
            existing.peak_avg_price = row.peak_avg_price
            existing.current_avg_price = row.current_avg_price
            existing.active_listings_count = row.active_listings_count
            existing.avg_drop_pct = row.avg_drop_pct
        else:
            db.add(
                BagIndexSnapshot(
                    brand=row.brand,
                    snapshot_date=row.snapshot_date,
                    index_value=row.index_value,
                    peak_avg_price=row.peak_avg_price,
                    current_avg_price=row.current_avg_price,
                    active_listings_count=row.active_listings_count,
                    avg_drop_pct=row.avg_drop_pct,
                )
            )

    db.commit()
    return rows
