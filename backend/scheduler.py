"""APScheduler setup — runs scrapers every 4 hours"""
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime, timedelta
from alerts import deliver_watch_alerts
from database import SessionLocal
from config import settings
from intelligence import persist_bag_index_snapshots
from models import Listing
from scrapers import (
    FashionphileScraper,
    LuxeDHScraper,
    MadisonAvenueCoutureScraper,
    RealRealScraper,
    RebagScraper,
    VestiaireScraper,
    YoogiScraper,
)


def deactivate_stale_listings(db, *, stale_after_hours: int | None = None) -> int:
    """Mark stale listings inactive when they have not been re-seen recently."""
    stale_after_hours = stale_after_hours or settings.public_listing_freshness_hours
    stale_cutoff = datetime.utcnow() - timedelta(hours=max(stale_after_hours, 1))
    stale_rows = (
        db.query(Listing)
        .filter(Listing.is_active == True, Listing.last_seen < stale_cutoff)
        .all()
    )

    for listing in stale_rows:
        listing.is_active = False

    if stale_rows:
        db.commit()

    return len(stale_rows)


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
    if settings.enable_yoogi:
        scrapers.append(YoogiScraper(db))
    if settings.enable_luxedh:
        scrapers.append(LuxeDHScraper(db))
    if settings.enable_madisonavenuecouture:
        scrapers.append(MadisonAvenueCoutureScraper(db))

    total = 0
    for scraper in scrapers:
        try:
            count = await scraper.scrape()
            total += count
        except Exception as e:
            print(f"[Scheduler] Scraper {scraper.__class__.__name__} failed: {e}")
        finally:
            await scraper.close()

    try:
        deactivated = deactivate_stale_listings(db)
        print(f"[Scheduler] Deactivated {deactivated} stale listings")
    except Exception as e:
        print(f"[Scheduler] Stale listing cleanup failed: {e}")

    try:
        rows = persist_bag_index_snapshots(db)
        print(f"[Scheduler] BagIndex refreshed for {len(rows)} brands")
    except Exception as e:
        print(f"[Scheduler] BagIndex refresh failed: {e}")

    db.close()
    print(f"[Scheduler] Done. Total listings processed: {total}")
    return total


def _smtp_is_configured() -> bool:
    return bool(settings.alert_from_email and settings.smtp_host)


def _parse_digest_recipients():
    from digest import parse_digest_recipients

    return parse_digest_recipients()


def _send_intelligence_digest(db, *, dry_run: bool = False):
    from digest import send_intelligence_digest

    return send_intelligence_digest(db, dry_run=dry_run)


async def run_watch_alert_job():
    """Send watchlist alerts on a fixed cadence when SMTP is configured."""
    if not settings.watch_alert_scheduler_enabled:
        return {"status": "skipped", "reason": "disabled"}
    if not _smtp_is_configured():
        return {"status": "skipped", "reason": "smtp_not_configured"}

    db = SessionLocal()
    try:
        result = deliver_watch_alerts(db, dry_run=False)
        print(
            "[Scheduler] Watch alerts sent to "
            f"{result['subscriptions_with_alerts']} subscriptions"
        )
        return {"status": "sent", **result}
    except Exception as e:
        db.rollback()
        print(f"[Scheduler] Watch alert job failed: {e}")
        raise
    finally:
        db.close()


async def run_intelligence_digest_job():
    """Send the intelligence digest on a daily cadence when configured."""
    if not settings.intelligence_digest_enabled:
        return {"status": "skipped", "reason": "disabled"}
    if not _parse_digest_recipients():
        return {"status": "skipped", "reason": "no_recipients"}
    if not _smtp_is_configured():
        return {"status": "skipped", "reason": "smtp_not_configured"}

    db = SessionLocal()
    try:
        result = _send_intelligence_digest(db, dry_run=False)
        print(
            "[Scheduler] Intelligence digest sent to "
            f"{result['recipient_count']} recipients"
        )
        return {"status": "sent", **result}
    except Exception as e:
        db.rollback()
        print(f"[Scheduler] Intelligence digest job failed: {e}")
        raise
    finally:
        db.close()


async def run_scraper(platform: str) -> int:
    """Run a single scraper by platform name"""
    db = SessionLocal()
    scraper_map = {
        "fashionphile": FashionphileScraper,
        "realreal": RealRealScraper,
        "rebag": RebagScraper,
        "vestiaire": VestiaireScraper,
        "yoogi": YoogiScraper,
        "luxedh": LuxeDHScraper,
        "madisonavenuecouture": MadisonAvenueCoutureScraper,
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
        trigger=IntervalTrigger(hours=settings.scraper_interval_hours),
        id="scrape_all",
        name="Scrape all platforms",
        replace_existing=True,
        misfire_grace_time=300,  # 5 min grace period
    )
    scheduler.add_job(
        run_watch_alert_job,
        trigger=IntervalTrigger(minutes=max(settings.watch_alert_interval_minutes, 5)),
        id="watch_alerts",
        name="Send watch alerts",
        replace_existing=True,
        misfire_grace_time=300,
    )
    scheduler.add_job(
        run_intelligence_digest_job,
        trigger=CronTrigger(
            hour=settings.intelligence_digest_hour_utc,
            minute=settings.intelligence_digest_minute_utc,
        ),
        id="intelligence_digest",
        name="Send intelligence digest",
        replace_existing=True,
        misfire_grace_time=1800,
    )
    return scheduler
