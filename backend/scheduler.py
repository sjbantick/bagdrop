"""APScheduler setup — runs scrapers every 4 hours"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
from database import SessionLocal
from config import settings
from scrapers import FashionphileScraper, RealRealScraper, RebagScraper, VestiaireScraper


async def run_all_scrapers():
    """Run all enabled scrapers sequentially"""
    db = SessionLocal()
    print(f"[Scheduler] Starting scrape run at {datetime.utcnow().isoformat()}")

    scrapers = []
    if settings.enable_fashionphile:
        scrapers.append(FashionphileScraper(db))
    if settings.enable_realreal:
        scrapers.append(RealRealScraper(db))
    if settings.enable_rebag:
        scrapers.append(RebagScraper(db))
    if settings.enable_vestiaire:
        scrapers.append(VestiaireScraper(db))

    total = 0
    for scraper in scrapers:
        try:
            count = await scraper.scrape()
            total += count
        except Exception as e:
            print(f"[Scheduler] Scraper {scraper.__class__.__name__} failed: {e}")
        finally:
            await scraper.close()

    db.close()
    print(f"[Scheduler] Done. Total listings processed: {total}")
    return total


async def run_scraper(platform: str) -> int:
    """Run a single scraper by platform name"""
    db = SessionLocal()
    scraper_map = {
        "fashionphile": FashionphileScraper,
        "realreal": RealRealScraper,
        "rebag": RebagScraper,
        "vestiaire": VestiaireScraper,
    }

    scraper_cls = scraper_map.get(platform.lower())
    if not scraper_cls:
        db.close()
        raise ValueError(f"Unknown platform: {platform}")

    scraper = scraper_cls(db)
    try:
        count = await scraper.scrape()
        return count
    finally:
        await scraper.close()
        db.close()


def create_scheduler() -> AsyncIOScheduler:
    """Create and configure the APScheduler"""
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        run_all_scrapers,
        trigger=IntervalTrigger(hours=4),
        id="scrape_all",
        name="Scrape all platforms",
        replace_existing=True,
        misfire_grace_time=300,  # 5 min grace period
    )
    return scheduler
