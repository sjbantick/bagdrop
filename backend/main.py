"""BagDrop FastAPI backend"""
from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_, func
from datetime import datetime, timedelta
from typing import List, Optional
from pydantic import BaseModel
import asyncio

from database import get_db, init_db
from models import Listing, PriceHistory, BagIndexSnapshot, VelocityScore
from config import settings
from scheduler import create_scheduler, run_all_scrapers, run_scraper

app = FastAPI(title="BagDrop API", version="0.1.0")
scheduler = create_scheduler()

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
    last_seen: datetime
    photo_url: Optional[str]

    class Config:
        from_attributes = True


class PriceHistoryResponse(BaseModel):
    price: float
    detected_at: datetime
    drop_pct: Optional[float]

    class Config:
        from_attributes = True


class BagIndexResponse(BaseModel):
    brand: str
    index_value: float
    snapshot_date: datetime
    current_avg_price: Optional[float]
    active_listings_count: Optional[int]

    class Config:
        from_attributes = True


@app.on_event("startup")
async def startup():
    """Initialize database on startup and start scheduler"""
    init_db()
    print("Database initialized")
    scheduler.start()
    print("Scheduler started — scraping every 4 hours")
    # Kick off an initial scrape in the background
    asyncio.create_task(run_all_scrapers())


@app.on_event("shutdown")
async def shutdown():
    scheduler.shutdown(wait=False)


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

    total = query.count()
    listings = query.limit(limit).offset(offset).all()

    return listings


@app.get("/api/listings/{listing_id}", response_model=ListingResponse)
async def get_listing(listing_id: str, db: Session = Depends(get_db)):
    """Get a specific listing"""
    listing = db.query(Listing).filter(Listing.id == listing_id).first()
    if not listing:
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
        .filter(Listing.is_active == True)
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
        .filter(and_(Listing.brand.ilike(brand), Listing.is_active == True))
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
        .filter(and_(Listing.id.in_(listing_ids), Listing.is_active == True))
        .order_by(desc(Listing.drop_pct))
        .limit(limit)
        .all()
    )
    return listings


@app.get("/api/bag-index", response_model=List[BagIndexResponse])
async def get_bag_index(
    limit: int = Query(20, le=100),
    days: int = Query(7, ge=1, le=90),
    db: Session = Depends(get_db),
):
    """Get latest BagIndex for top brands"""
    time_cutoff = datetime.utcnow() - timedelta(days=days)

    snapshots = (
        db.query(BagIndexSnapshot)
        .filter(BagIndexSnapshot.snapshot_date >= time_cutoff)
        .order_by(desc(BagIndexSnapshot.snapshot_date), BagIndexSnapshot.index_value)
        .limit(limit)
        .all()
    )
    return snapshots


@app.get("/api/stats")
async def get_stats(db: Session = Depends(get_db)):
    """Get overall stats for the header display"""
    total_active = db.query(func.count(Listing.id)).filter(Listing.is_active == True).scalar() or 0
    avg_drop = db.query(func.avg(Listing.drop_pct)).filter(
        and_(Listing.is_active == True, Listing.drop_pct > 0)
    ).scalar()
    biggest_drop = db.query(func.max(Listing.drop_pct)).filter(Listing.is_active == True).scalar()
    return {
        "total_active_listings": total_active,
        "avg_drop_pct": round(float(avg_drop), 1) if avg_drop else None,
        "biggest_drop_pct": round(float(biggest_drop), 1) if biggest_drop else None,
    }


@app.post("/api/admin/scrape")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    platform: Optional[str] = Query(None, description="Specific platform to scrape (or all if omitted)"),
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
