"""One-time script: normalize brand names in the database to fix casing."""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from database import SessionLocal, engine, Base
from models import Listing, BagIndexSnapshot
from scrapers.base import BaseScraper

# Instantiate a throwaway scraper just to use normalize_brand
class _Normalizer(BaseScraper):
    platform = None
    base_url = ""
    def scrape(self, db): pass

norm = _Normalizer.__new__(_Normalizer)

db = SessionLocal()
try:
    listings = db.query(Listing).all()
    updated = 0
    for listing in listings:
        normalized = norm.normalize_brand(listing.brand or "")
        if normalized != listing.brand:
            listing.brand = normalized
            updated += 1
    db.commit()
    print(f"Updated {updated} of {len(listings)} listings.")

    # Also fix BagIndexSnapshot
    snapshots = db.query(BagIndexSnapshot).all()
    snap_updated = 0
    for snap in snapshots:
        normalized = norm.normalize_brand(snap.brand or "")
        if normalized != snap.brand:
            snap.brand = normalized
            snap_updated += 1
    db.commit()
    print(f"Updated {snap_updated} BagIndexSnapshot rows.")
finally:
    db.close()
