"""Base scraper class and utilities"""
import asyncio
import random
from typing import Optional, List
from abc import ABC, abstractmethod
from datetime import datetime
from sqlalchemy.orm import Session
from models import Listing, PriceHistory, Scrape, Platform, ConditionGrade
from config import settings
import httpx


USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Safari/605.1.15",
]


class BaseScraper(ABC):
    """Base class for all platform scrapers"""

    platform: Platform
    base_url: str

    def __init__(self, db: Session):
        self.db = db
        self.http_client = httpx.AsyncClient(timeout=settings.scraper_timeout)

    async def close(self):
        """Close HTTP client"""
        await self.http_client.aclose()

    def get_headers(self) -> dict:
        """Get headers with random user agent"""
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
        }

    async def fetch(self, url: str) -> Optional[str]:
        """Fetch a URL with retry logic"""
        for attempt in range(settings.scraper_retry_count):
            try:
                await asyncio.sleep(settings.scraper_rate_limit_delay)
                response = await self.http_client.get(url, headers=self.get_headers(), follow_redirects=True)
                if response.status_code == 200:
                    return response.text
                else:
                    print(f"Failed to fetch {url}: {response.status_code}")
            except Exception as e:
                print(f"Error fetching {url} (attempt {attempt + 1}): {e}")
                if attempt < settings.scraper_retry_count - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
        return None

    @abstractmethod
    async def scrape(self) -> int:
        """Scrape listings from this platform. Return count of new/updated listings"""
        pass

    def normalize_brand(self, brand: str) -> str:
        """Normalize brand name for consistency"""
        brand = brand.strip().lower()
        # Common aliases
        aliases = {
            "hermes": "hermès",
            "louis vuitton": "louis vuitton",
            "lv": "louis vuitton",
            "bottega veneta": "bottega veneta",
            "bv": "bottega veneta",
            "celine": "céline",
            "loewe": "loewe",
            "prada": "prada",
        }
        return aliases.get(brand, brand.title())

    def normalize_model(self, model: str) -> str:
        """Normalize model name"""
        return model.strip().lower()

    def save_listing(
        self,
        platform_id: str,
        brand: str,
        model: str,
        url: str,
        current_price: float,
        original_price: Optional[float] = None,
        size: Optional[str] = None,
        color: Optional[str] = None,
        hardware: Optional[str] = None,
        condition: str = "good",
        description: Optional[str] = None,
        photo_url: Optional[str] = None,
    ) -> bool:
        """Save or update a listing. Return True if new."""
        listing_id = f"{self.platform.value}_{platform_id}"

        # Check if exists
        existing = self.db.query(Listing).filter(Listing.id == listing_id).first()

        brand = self.normalize_brand(brand)
        model = self.normalize_model(model)
        original_price = original_price or current_price
        # Store as positive percentage drop (10.5 = 10.5% off)
        drop_amount = original_price - current_price
        drop_pct = (drop_amount / original_price * 100) if original_price > 0 else 0

        if existing:
            # Capture old price before update
            old_price = existing.current_price

            # Update existing listing
            existing.current_price = current_price
            existing.drop_amount = drop_amount
            existing.drop_pct = drop_pct
            existing.last_seen = datetime.utcnow()
            existing.last_price_check = datetime.utcnow()
            existing.is_active = True

            # Add to price history if price changed
            if old_price != current_price:
                price_history = PriceHistory(
                    listing_id=listing_id,
                    platform=self.platform.value,
                    price=current_price,
                    original_price=original_price,
                    drop_pct=drop_pct,
                )
                self.db.add(price_history)

            self.db.commit()
            return False
        else:
            # Create new listing
            listing = Listing(
                id=listing_id,
                platform=self.platform.value,
                platform_id=platform_id,
                url=url,
                brand=brand,
                model=model,
                size=size,
                color=color,
                hardware=hardware,
                condition=condition,
                current_price=current_price,
                original_price=original_price,
                drop_amount=drop_amount,
                drop_pct=drop_pct,
                description=description,
                photo_url=photo_url,
            )
            self.db.add(listing)

            # Add initial price history
            price_history = PriceHistory(
                listing_id=listing_id,
                platform=self.platform.value,
                price=current_price,
                original_price=original_price,
                drop_pct=drop_pct,
            )
            self.db.add(price_history)
            self.db.commit()
            return True

    def log_scrape(self, success: bool, listings_found: int, listings_new: int, listings_updated: int, error: Optional[str] = None):
        """Log scrape run"""
        scrape = Scrape(
            platform=self.platform.value,
            listings_found=listings_found,
            listings_new=listings_new,
            listings_updated=listings_updated,
            success=success,
            error_message=error,
            completed_at=datetime.utcnow(),
        )
        self.db.add(scrape)
        self.db.commit()
