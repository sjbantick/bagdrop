from pathlib import Path
import sys

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from main import (  # noqa: E402
    ListingReportRequest,
    WatchSubscriptionRequest,
    _build_arbitrage_opportunities,
    _build_intelligence_brief,
    _build_market_velocity,
    _build_new_drop_opportunities,
    _build_top_clicks,
    _normalize_watch_email,
    _affiliate_query_for_platform,
    _build_outbound_target_url,
    report_listing_issue,
    _resolve_market,
    get_listing,
    get_listings,
    get_ops_summary,
    subscribe_to_watchlist,
)
from alerts import deliver_watch_alerts, get_pending_watch_alerts, resolve_watch_unsubscribe_token  # noqa: E402
from config import settings  # noqa: E402
from digest import parse_digest_recipients, render_intelligence_digest, send_intelligence_digest  # noqa: E402
from intelligence import compute_bag_index_rows, persist_bag_index_snapshots  # noqa: E402
from models import Base, BagIndexSnapshot, Listing, ListingReport, WatchAlertDelivery, WatchSubscription  # noqa: E402
from models import OutboundClick  # noqa: E402
import scheduler as scheduler_module  # noqa: E402
from scheduler import deactivate_stale_listings  # noqa: E402
from utils import market_path, slugify_text  # noqa: E402
from datetime import datetime, timedelta


@pytest.fixture
def anyio_backend():
    return "asyncio"


def make_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    return sessionmaker(bind=engine)()


def make_request(client_host: str = "127.0.0.1", user_agent: str = "pytest"):
    class Client:
        host = client_host

    class Request:
        client = Client()
        headers = {"user-agent": user_agent}

    return Request()


def test_slugify_text_normalizes_unicode_and_spacing():
    assert slugify_text("Hermès Kelly Sellier 28") == "hermes-kelly-sellier-28"
    assert slugify_text("Céline  Triomphe / Small") == "celine-triomphe-small"
    assert market_path("Hermès", "Kelly Sellier 28") == "/hermes/kelly-sellier-28"


def test_resolve_market_matches_canonical_slugs():
    session = make_session()
    session.add(
        Listing(
            id="fashionphile_1",
            platform="fashionphile",
            platform_id="1",
            url="https://example.com/listing",
            brand="Hermès",
            model="kelly sellier 28",
            condition="excellent",
            current_price=12000,
            original_price=15000,
            drop_amount=3000,
            drop_pct=20,
            is_active=True,
        )
    )
    session.commit()

    assert _resolve_market(session, "hermes", "kelly-sellier-28") == ("Hermès", "kelly sellier 28")


def test_build_outbound_target_url_adds_tracking_params():
    listing = Listing(
        id="rebag_1",
        platform="rebag",
        platform_id="1",
        url="https://example.com/listing?existing=1",
        brand="Chanel",
        model="classic flap",
        condition="good",
        current_price=8000,
    )

    outbound_url = _build_outbound_target_url(listing, surface="listing_card", context="feed")

    assert "existing=1" in outbound_url
    assert "utm_source=bagdrop" in outbound_url
    assert "utm_medium=marketplace_click" in outbound_url
    assert "utm_campaign=rebag" in outbound_url
    assert "utm_content=listing_card" in outbound_url
    assert "utm_term=feed" in outbound_url


def test_affiliate_query_for_platform_parses_env_value():
    original = settings.rebag_affiliate_query
    settings.rebag_affiliate_query = "?ref=bagdrop&campaign=launch"
    try:
        assert _affiliate_query_for_platform("rebag") == {
            "ref": "bagdrop",
            "campaign": "launch",
        }
    finally:
        settings.rebag_affiliate_query = original


def test_affiliate_query_for_platform_renders_placeholders():
    original = settings.rebag_affiliate_query
    settings.rebag_affiliate_query = "?subid={{listing_id}}&surface={{surface}}&market={{brand_slug}}-{{model_slug}}"
    try:
        assert _affiliate_query_for_platform(
            "rebag",
            {
                "listing_id": "rebag_42",
                "surface": "listing_card",
                "brand_slug": "hermes",
                "model_slug": "kelly-28",
            },
        ) == {
            "subid": "rebag_42",
            "surface": "listing_card",
            "market": "hermes-kelly-28",
        }
    finally:
        settings.rebag_affiliate_query = original


def test_compute_bag_index_rows_normalizes_negative_zero_delta():
    session = make_session()
    snapshot_time = datetime.utcnow() - timedelta(hours=2)
    session.add(
        Listing(
            id="fashionphile_1",
            platform="fashionphile",
            platform_id="1",
            url="https://example.com/listing/1",
            brand="Bottega Veneta",
            model="Andiamo",
            condition="excellent",
            current_price=5000,
            original_price=6200,
            drop_amount=1200,
            drop_pct=19.4,
            is_active=True,
        )
    )
    session.add(
        BagIndexSnapshot(
            brand="Bottega Veneta",
            snapshot_date=snapshot_time,
            index_value=100.0,
            peak_avg_price=5000,
            current_avg_price=5000,
            active_listings_count=1,
            avg_drop_pct=19.4,
        )
    )
    session.commit()

    rows = compute_bag_index_rows(session, limit=5, min_active_listings=1, snapshot_time=datetime.utcnow())

    assert rows[0].delta_pct == 0.0
    assert rows[0].trend == "flat"


def test_deactivate_stale_listings_marks_old_inventory_inactive():
    session = make_session()
    now = datetime.utcnow()
    session.add_all([
        Listing(
            id="fresh_1",
            platform="fashionphile",
            platform_id="fresh_1",
            url="https://example.com/fresh",
            brand="Chanel",
            model="Classic Flap",
            condition="good",
            current_price=7000,
            original_price=9000,
            drop_amount=2000,
            drop_pct=22.2,
            is_active=True,
            last_seen=now,
        ),
        Listing(
            id="stale_1",
            platform="fashionphile",
            platform_id="stale_1",
            url="https://example.com/stale",
            brand="Chanel",
            model="Classic Flap",
            condition="good",
            current_price=6800,
            original_price=9000,
            drop_amount=2200,
            drop_pct=24.4,
            is_active=True,
            last_seen=now - timedelta(hours=16),
        ),
    ])
    session.commit()

    deactivated = deactivate_stale_listings(session, stale_after_hours=12)
    fresh = session.query(Listing).filter(Listing.id == "fresh_1").one()
    stale = session.query(Listing).filter(Listing.id == "stale_1").one()

    assert deactivated == 1
    assert fresh.is_active is True
    assert stale.is_active is False


@pytest.mark.anyio
async def test_public_listing_queries_hide_stale_inventory():
    session = make_session()
    now = datetime.utcnow()
    session.add_all([
        Listing(
            id="fresh_1",
            platform="fashionphile",
            platform_id="fresh_1",
            url="https://example.com/fresh",
            brand="Chanel",
            model="Classic Flap",
            condition="good",
            current_price=7000,
            original_price=9000,
            drop_amount=2000,
            drop_pct=22.2,
            is_active=True,
            last_seen=now,
        ),
        Listing(
            id="stale_1",
            platform="fashionphile",
            platform_id="stale_1",
            url="https://example.com/stale",
            brand="Chanel",
            model="Classic Flap",
            condition="good",
            current_price=6800,
            original_price=9000,
            drop_amount=2200,
            drop_pct=24.4,
            is_active=True,
            last_seen=now - timedelta(hours=16),
        ),
    ])
    session.commit()

    listings = await get_listings(
        db=session,
        brand=None,
        model=None,
        platform=None,
        min_drop_pct=0,
        max_drop_pct=100,
        sort_by="drop_pct",
        limit=50,
        offset=0,
    )

    assert [listing.id for listing in listings] == ["fresh_1"]
    with pytest.raises(HTTPException) as exc:
        await get_listing("stale_1", db=session)
    assert exc.value.status_code == 404


@pytest.mark.anyio
async def test_subscribe_to_watchlist_creates_and_deduplicates():
    session = make_session()

    first = await subscribe_to_watchlist(
        WatchSubscriptionRequest(
            email="buyer@example.com",
            brand="Hermès",
            model="Kelly Sellier 28",
            source="market_page",
        ),
        session,
    )
    second = await subscribe_to_watchlist(
        WatchSubscriptionRequest(
            email="buyer@example.com",
            brand="Hermès",
            model="Kelly Sellier 28",
            source="market_page",
        ),
        session,
    )

    assert first.already_subscribed is False
    assert second.already_subscribed is True
    assert first.canonical_path == "/hermes/kelly-sellier-28"
    assert second.id == first.id


@pytest.mark.anyio
async def test_report_listing_issue_logs_report_without_hiding_fresh_listing():
    session = make_session()
    session.add(
        Listing(
            id="fashionphile_1",
            platform="fashionphile",
            platform_id="1",
            url="https://example.com/listing/1",
            brand="Hermès",
            model="Kelly Sellier 28",
            condition="excellent",
            current_price=12000,
            original_price=15000,
            drop_amount=3000,
            drop_pct=20,
            is_active=True,
            last_seen=datetime.utcnow(),
        )
    )
    session.commit()

    response = await report_listing_issue(
        "fashionphile_1",
        ListingReportRequest(reason="sold", source="listing_detail"),
        make_request(),
        session,
    )

    listing = session.query(Listing).filter(Listing.id == "fashionphile_1").one()
    reports = session.query(ListingReport).filter(ListingReport.listing_id == "fashionphile_1").all()

    assert response.listing_hidden is False
    assert response.report_count_7d == 1
    assert listing.is_active is True
    assert len(reports) == 1


@pytest.mark.anyio
async def test_report_listing_issue_hides_listing_after_threshold():
    session = make_session()
    listing = Listing(
        id="fashionphile_1",
        platform="fashionphile",
        platform_id="1",
        url="https://example.com/listing/1",
        brand="Hermès",
        model="Kelly Sellier 28",
        condition="excellent",
        current_price=12000,
        original_price=15000,
        drop_amount=3000,
        drop_pct=20,
        is_active=True,
        last_seen=datetime.utcnow(),
    )
    session.add(listing)
    session.commit()

    session.add(
        ListingReport(
            listing_id="fashionphile_1",
            platform="fashionphile",
            reason="sold",
            source="listing_detail",
        )
    )
    session.commit()

    response = await report_listing_issue(
        "fashionphile_1",
        ListingReportRequest(reason="dead", source="listing_detail"),
        make_request(client_host="127.0.0.2"),
        session,
    )

    updated = session.query(Listing).filter(Listing.id == "fashionphile_1").one()

    assert response.listing_hidden is True
    assert response.report_count_7d == 2
    assert updated.is_active is False


@pytest.mark.anyio
async def test_unsubscribe_token_round_trip():
    session = make_session()
    subscription = await subscribe_to_watchlist(
        WatchSubscriptionRequest(
            email="buyer@example.com",
            brand="Hermès",
            model="Kelly Sellier 28",
            source="market_page",
        ),
        session,
    )

    model = resolve_watch_unsubscribe_token(subscription.unsubscribe_url.split("token=")[1], session)
    assert model is not None
    assert model.email == "buyer@example.com"


@pytest.mark.anyio
async def test_deliver_watch_alerts_dry_run_and_dedupe():
    session = make_session()
    subscription = await subscribe_to_watchlist(
        WatchSubscriptionRequest(
            email="buyer@example.com",
            brand="Hermès",
            model="Kelly Sellier 28",
            source="market_page",
        ),
        session,
    )
    session.add_all([
        Listing(
            id="fashionphile_1",
            platform="fashionphile",
            platform_id="1",
            url="https://example.com/listing/1",
            brand="Hermès",
            model="Kelly Sellier 28",
            condition="excellent",
            current_price=12000,
            original_price=15000,
            drop_amount=3000,
            drop_pct=20,
            is_active=True,
        ),
        Listing(
            id="rebag_1",
            platform="rebag",
            platform_id="2",
            url="https://example.com/listing/2",
            brand="Hermès",
            model="Kelly Sellier 28",
            condition="good",
            current_price=11000,
            original_price=14500,
            drop_amount=3500,
            drop_pct=24.1,
            is_active=True,
        ),
    ])
    session.commit()

    summary = deliver_watch_alerts(session, dry_run=True)
    assert summary["subscriptions_with_alerts"] == 1
    assert summary["deliveries"][0]["listing_count"] == 2

    session.add(WatchAlertDelivery(
        watch_subscription_id=subscription.id,
        listing_id="fashionphile_1",
        email="buyer@example.com",
    ))
    session.commit()

    summary_after = deliver_watch_alerts(session, dry_run=True)
    assert summary_after["deliveries"][0]["listing_count"] == 1


@pytest.mark.anyio
async def test_watch_alerts_only_include_fresh_listings_after_subscription():
    session = make_session()
    subscription = await subscribe_to_watchlist(
        WatchSubscriptionRequest(
            email="buyer@example.com",
            brand="Hermès",
            model="Kelly Sellier 28",
            source="market_page",
        ),
        session,
    )

    session.add_all([
        Listing(
            id="fashionphile_old",
            platform="fashionphile",
            platform_id="1",
            url="https://example.com/listing/old",
            brand="Hermès",
            model="Kelly Sellier 28",
            condition="excellent",
            current_price=12000,
            first_seen=subscription.created_at - timedelta(hours=3),
            is_active=True,
        ),
        Listing(
            id="fashionphile_new",
            platform="fashionphile",
            platform_id="2",
            url="https://example.com/listing/new",
            brand="Hermès",
            model="Kelly Sellier 28",
            condition="excellent",
            current_price=11800,
            first_seen=subscription.created_at + timedelta(minutes=5),
            is_active=True,
        ),
    ])
    session.commit()

    pending = get_pending_watch_alerts(session)

    assert len(pending) == 1
    assert [listing.id for listing in pending[0].listings] == ["fashionphile_new"]


@pytest.mark.anyio
async def test_watch_alerts_respect_cooldown_window():
    session = make_session()
    subscription = await subscribe_to_watchlist(
        WatchSubscriptionRequest(
            email="buyer@example.com",
            brand="Hermès",
            model="Kelly Sellier 28",
            source="market_page",
        ),
        session,
    )
    subscription_model = session.query(WatchSubscription).filter(WatchSubscription.id == subscription.id).one()
    subscription_model.last_notified_at = datetime.utcnow()
    session.add(
        Listing(
            id="fashionphile_new",
            platform="fashionphile",
            platform_id="2",
            url="https://example.com/listing/new",
            brand="Hermès",
            model="Kelly Sellier 28",
            condition="excellent",
            current_price=11800,
            first_seen=datetime.utcnow(),
            is_active=True,
        )
    )
    session.commit()

    pending = get_pending_watch_alerts(session)

    assert pending == []


def test_normalize_watch_email_rejects_invalid_input():
    with pytest.raises(HTTPException):
        _normalize_watch_email("not-an-email")


def test_build_arbitrage_opportunities_surfaces_underpriced_listing():
    session = make_session()
    session.add_all([
        Listing(
            id="fashionphile_1",
            platform="fashionphile",
            platform_id="1",
            url="https://example.com/listing/1",
            brand="Chanel",
            model="Classic Flap",
            condition="excellent",
            current_price=7000,
            original_price=9000,
            drop_amount=2000,
            drop_pct=22.2,
            is_active=True,
        ),
        Listing(
            id="rebag_1",
            platform="rebag",
            platform_id="2",
            url="https://example.com/listing/2",
            brand="Chanel",
            model="Classic Flap",
            condition="good",
            current_price=10000,
            original_price=11200,
            drop_amount=1200,
            drop_pct=10.7,
            is_active=True,
        ),
        Listing(
            id="realreal_1",
            platform="realreal",
            platform_id="3",
            url="https://example.com/listing/3",
            brand="Chanel",
            model="Classic Flap",
            condition="good",
            current_price=9500,
            original_price=11000,
            drop_amount=1500,
            drop_pct=13.6,
            is_active=True,
        ),
    ])
    session.commit()

    opportunities = _build_arbitrage_opportunities(
        session,
        limit=5,
        min_market_listings=3,
        min_platforms=2,
        min_gap_pct=15,
    )

    assert len(opportunities) == 1
    assert opportunities[0].listing.id == "fashionphile_1"
    assert opportunities[0].canonical_path == "/chanel/classic-flap"
    assert opportunities[0].market_platform_count == 3
    assert opportunities[0].market_gap_pct > 20


def test_build_market_velocity_scores_recent_supply_pressure():
    session = make_session()
    now = datetime.utcnow()
    session.add_all([
        Listing(
            id="fashionphile_1",
            platform="fashionphile",
            platform_id="1",
            url="https://example.com/listing/1",
            brand="Chanel",
            model="Classic Flap",
            condition="excellent",
            current_price=7000,
            first_seen=now - timedelta(days=3),
            is_active=True,
        ),
        Listing(
            id="rebag_1",
            platform="rebag",
            platform_id="2",
            url="https://example.com/listing/2",
            brand="Chanel",
            model="Classic Flap",
            condition="good",
            current_price=10000,
            first_seen=now - timedelta(days=12),
            is_active=True,
        ),
        Listing(
            id="realreal_1",
            platform="realreal",
            platform_id="3",
            url="https://example.com/listing/3",
            brand="Chanel",
            model="Classic Flap",
            condition="good",
            current_price=9500,
            first_seen=now - timedelta(days=40),
            is_active=True,
        ),
        Listing(
            id="vestiaire_1",
            platform="vestiaire",
            platform_id="4",
            url="https://example.com/listing/4",
            brand="Chanel",
            model="Classic Flap",
            condition="good",
            current_price=9800,
            first_seen=now - timedelta(days=80),
            is_active=True,
        ),
    ])
    session.commit()

    velocity = _build_market_velocity(session, "Chanel", "Classic Flap")

    assert velocity.canonical_path == "/chanel/classic-flap"
    assert velocity.active_listings == 4
    assert velocity.platform_count == 4
    assert velocity.recent_listings_7d == 1
    assert velocity.recent_listings_30d == 2
    assert velocity.recent_listings_60d == 3
    assert velocity.recent_listings_90d == 4
    assert velocity.velocity_score > 50
    assert velocity.velocity_label in {"active", "hot"}


def test_compute_bag_index_rows_uses_previous_peak_price():
    session = make_session()
    now = datetime.utcnow()
    session.add_all([
        Listing(
            id="fashionphile_1",
            platform="fashionphile",
            platform_id="1",
            url="https://example.com/listing/1",
            brand="Chanel",
            model="Classic Flap",
            condition="excellent",
            current_price=8000,
            first_seen=now - timedelta(days=4),
            is_active=True,
            drop_pct=20,
        ),
        Listing(
            id="rebag_1",
            platform="rebag",
            platform_id="2",
            url="https://example.com/listing/2",
            brand="Chanel",
            model="Boy Bag",
            condition="good",
            current_price=10000,
            first_seen=now - timedelta(days=10),
            is_active=True,
            drop_pct=12,
        ),
    ])
    session.add(
        BagIndexSnapshot(
            brand="Chanel",
            snapshot_date=now - timedelta(days=7),
            index_value=100,
            peak_avg_price=12000,
            current_avg_price=12000,
            active_listings_count=2,
            avg_drop_pct=8,
        )
    )
    session.commit()

    rows = compute_bag_index_rows(session, limit=5, min_active_listings=1)
    chanel = next(row for row in rows if row.brand == "Chanel")

    assert chanel.peak_avg_price == 12000
    assert chanel.current_avg_price == 9000
    assert chanel.index_value == 75.0
    assert chanel.previous_index_value == 100.0
    assert chanel.delta_pct == -25.0
    assert chanel.trend == "down"


def test_persist_bag_index_snapshots_updates_same_day_snapshot():
    session = make_session()
    now = datetime.utcnow()
    session.add(
        Listing(
            id="fashionphile_1",
            platform="fashionphile",
            platform_id="1",
            url="https://example.com/listing/1",
            brand="Hermès",
            model="Kelly 28",
            condition="excellent",
            current_price=15000,
            first_seen=now - timedelta(days=2),
            is_active=True,
            drop_pct=10,
        )
    )
    session.commit()

    first_rows = persist_bag_index_snapshots(session, limit=5, min_active_listings=1, snapshot_time=now)
    second_rows = persist_bag_index_snapshots(
        session,
        limit=5,
        min_active_listings=1,
        snapshot_time=now + timedelta(hours=2),
    )

    snapshots = session.query(BagIndexSnapshot).filter(BagIndexSnapshot.brand == "Hermès").all()
    assert len(snapshots) == 1
    assert len(first_rows) == 1
    assert len(second_rows) == 1


def test_build_new_drop_opportunities_ranks_fresh_discounted_listings():
    session = make_session()
    now = datetime.utcnow()
    session.add_all([
        Listing(
            id="fashionphile_1",
            platform="fashionphile",
            platform_id="1",
            url="https://example.com/listing/1",
            brand="Louis Vuitton",
            model="Capucines",
            condition="excellent",
            current_price=5000,
            original_price=7500,
            drop_amount=2500,
            drop_pct=33.3,
            first_seen=now - timedelta(hours=4),
            is_active=True,
        ),
        Listing(
            id="rebag_1",
            platform="rebag",
            platform_id="2",
            url="https://example.com/listing/2",
            brand="Louis Vuitton",
            model="Capucines",
            condition="good",
            current_price=7800,
            original_price=8200,
            drop_amount=400,
            drop_pct=4.9,
            first_seen=now - timedelta(hours=5),
            is_active=True,
        ),
        Listing(
            id="realreal_1",
            platform="realreal",
            platform_id="3",
            url="https://example.com/listing/3",
            brand="Louis Vuitton",
            model="Capucines",
            condition="good",
            current_price=7600,
            original_price=8600,
            drop_amount=1000,
            drop_pct=11.6,
            first_seen=now - timedelta(hours=8),
            is_active=True,
        ),
    ])
    session.commit()

    opportunities = _build_new_drop_opportunities(session, hours=72, limit=5, min_significance=30)

    assert len(opportunities) >= 1
    assert opportunities[0].listing.id == "fashionphile_1"
    assert opportunities[0].hours_since_first_seen < 5
    assert opportunities[0].market_platform_count == 3
    assert opportunities[0].significance_score >= 40


def test_build_intelligence_brief_combines_signals():
    session = make_session()
    now = datetime.utcnow()
    session.add_all([
        Listing(
            id="fashionphile_1",
            platform="fashionphile",
            platform_id="1",
            url="https://example.com/listing/1",
            brand="Bottega Veneta",
            model="Jodie",
            condition="excellent",
            current_price=1800,
            original_price=2600,
            drop_amount=800,
            drop_pct=30.8,
            first_seen=now - timedelta(hours=6),
            is_active=True,
        ),
        Listing(
            id="rebag_1",
            platform="rebag",
            platform_id="2",
            url="https://example.com/listing/2",
            brand="Bottega Veneta",
            model="Jodie",
            condition="good",
            current_price=2400,
            original_price=2800,
            drop_amount=400,
            drop_pct=14.3,
            first_seen=now - timedelta(hours=12),
            is_active=True,
        ),
        Listing(
            id="realreal_1",
            platform="realreal",
            platform_id="3",
            url="https://example.com/listing/3",
            brand="Bottega Veneta",
            model="Jodie",
            condition="good",
            current_price=2500,
            original_price=3100,
            drop_amount=600,
            drop_pct=19.4,
            first_seen=now - timedelta(hours=18),
            is_active=True,
        ),
    ])
    session.add(
        BagIndexSnapshot(
            brand="Bottega Veneta",
            snapshot_date=now - timedelta(days=1),
            index_value=95,
            peak_avg_price=2500,
            current_avg_price=2375,
            active_listings_count=3,
            avg_drop_pct=12,
        )
    )
    session.commit()

    brief = _build_intelligence_brief(session, arbitrage_limit=3, new_drop_limit=3, bag_index_limit=3)

    assert brief.arbitrage
    assert brief.new_drops
    assert brief.bag_index_movers


def test_parse_digest_recipients_splits_comma_list():
    assert parse_digest_recipients("a@example.com, b@example.com ,,c@example.com") == [
        "a@example.com",
        "b@example.com",
        "c@example.com",
    ]


def test_send_intelligence_digest_dry_run_uses_brief():
    session = make_session()
    now = datetime.utcnow()
    session.add_all([
        Listing(
            id="fashionphile_1",
            platform="fashionphile",
            platform_id="1",
            url="https://example.com/listing/1",
            brand="Prada",
            model="Galleria",
            condition="excellent",
            current_price=1800,
            original_price=2400,
            drop_amount=600,
            drop_pct=25,
            first_seen=now - timedelta(hours=5),
            is_active=True,
        ),
        Listing(
            id="rebag_1",
            platform="rebag",
            platform_id="2",
            url="https://example.com/listing/2",
            brand="Prada",
            model="Galleria",
            condition="good",
            current_price=2400,
            original_price=2900,
            drop_amount=500,
            drop_pct=17.2,
            first_seen=now - timedelta(hours=12),
            is_active=True,
        ),
        Listing(
            id="realreal_1",
            platform="realreal",
            platform_id="3",
            url="https://example.com/listing/3",
            brand="Prada",
            model="Galleria",
            condition="good",
            current_price=2350,
            original_price=2800,
            drop_amount=450,
            drop_pct=16.1,
            first_seen=now - timedelta(hours=20),
            is_active=True,
        ),
    ])
    session.commit()

    original = settings.intelligence_digest_recipients
    settings.intelligence_digest_recipients = "team@example.com"
    try:
        summary = send_intelligence_digest(session, dry_run=True)
    finally:
        settings.intelligence_digest_recipients = original

    assert summary["dry_run"] is True
    assert summary["recipient_count"] == 1
    assert summary["arbitrage_count"] >= 1
    assert summary["new_drop_count"] >= 1


def test_build_top_clicks_summarizes_listings_and_markets():
    session = make_session()
    now = datetime.utcnow()
    session.add_all([
        Listing(
            id="fashionphile_1",
            platform="fashionphile",
            platform_id="1",
            url="https://example.com/listing/1",
            brand="Chanel",
            model="Classic Flap",
            condition="excellent",
            current_price=7000,
            is_active=True,
        ),
        Listing(
            id="rebag_1",
            platform="rebag",
            platform_id="2",
            url="https://example.com/listing/2",
            brand="Chanel",
            model="Classic Flap",
            condition="good",
            current_price=9000,
            is_active=True,
        ),
    ])
    session.flush()
    session.add_all([
        OutboundClick(
            listing_id="fashionphile_1",
            platform="fashionphile",
            surface="listing_card",
            context="feed",
            target_url="https://example.com/listing/1",
            created_at=now - timedelta(days=1),
        ),
        OutboundClick(
            listing_id="fashionphile_1",
            platform="fashionphile",
            surface="listing_card",
            context="feed",
            target_url="https://example.com/listing/1",
            created_at=now - timedelta(hours=3),
        ),
        OutboundClick(
            listing_id="rebag_1",
            platform="rebag",
            surface="listing_detail",
            context="listing_page",
            target_url="https://example.com/listing/2",
            created_at=now - timedelta(hours=2),
        ),
    ])
    session.commit()

    summary = _build_top_clicks(session, days=7, limit=5)

    assert summary.listings[0].listing_id == "fashionphile_1"
    assert summary.listings[0].click_count == 2
    assert summary.markets[0].canonical_path == "/chanel/classic-flap"
    assert summary.markets[0].click_count == 3
    assert summary.platforms[0].platform == "fashionphile"
    assert summary.platforms[0].click_count == 2
    assert summary.platforms[0].unique_listings == 1
    assert summary.platforms[0].unique_markets == 1
    assert summary.surfaces[0].surface == "listing_card"
    assert summary.surfaces[0].unique_listings == 1
    assert summary.surfaces[0].unique_markets == 1
    assert summary.contexts[0].context == "feed"
    assert summary.contexts[0].click_count == 2


@pytest.mark.anyio
async def test_run_watch_alert_job_skips_when_smtp_missing():
    original_from = settings.alert_from_email
    original_host = settings.smtp_host
    original_enabled = settings.watch_alert_scheduler_enabled
    settings.alert_from_email = ""
    settings.smtp_host = ""
    settings.watch_alert_scheduler_enabled = True
    try:
        summary = await scheduler_module.run_watch_alert_job()
    finally:
        settings.alert_from_email = original_from
        settings.smtp_host = original_host
        settings.watch_alert_scheduler_enabled = original_enabled

    assert summary == {"status": "skipped", "reason": "smtp_not_configured"}


@pytest.mark.anyio
async def test_run_watch_alert_job_sends_when_configured(monkeypatch):
    class DummySession:
        def rollback(self):
            pass

        def close(self):
            pass

    original_from = settings.alert_from_email
    original_host = settings.smtp_host
    original_enabled = settings.watch_alert_scheduler_enabled
    settings.alert_from_email = "alerts@example.com"
    settings.smtp_host = "smtp.example.com"
    settings.watch_alert_scheduler_enabled = True

    monkeypatch.setattr(scheduler_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(
        scheduler_module,
        "deliver_watch_alerts",
        lambda db, dry_run=False: {
            "dry_run": dry_run,
            "subscriptions_with_alerts": 2,
            "deliveries": [],
        },
    )
    try:
        summary = await scheduler_module.run_watch_alert_job()
    finally:
        settings.alert_from_email = original_from
        settings.smtp_host = original_host
        settings.watch_alert_scheduler_enabled = original_enabled

    assert summary["status"] == "sent"
    assert summary["subscriptions_with_alerts"] == 2


@pytest.mark.anyio
async def test_run_intelligence_digest_job_skips_without_recipients():
    original_enabled = settings.intelligence_digest_enabled
    original_recipients = settings.intelligence_digest_recipients
    original_from = settings.alert_from_email
    original_host = settings.smtp_host
    settings.intelligence_digest_enabled = True
    settings.intelligence_digest_recipients = ""
    settings.alert_from_email = "alerts@example.com"
    settings.smtp_host = "smtp.example.com"
    try:
        summary = await scheduler_module.run_intelligence_digest_job()
    finally:
        settings.intelligence_digest_enabled = original_enabled
        settings.intelligence_digest_recipients = original_recipients
        settings.alert_from_email = original_from
        settings.smtp_host = original_host

    assert summary == {"status": "skipped", "reason": "no_recipients"}


@pytest.mark.anyio
async def test_run_intelligence_digest_job_sends_when_configured(monkeypatch):
    class DummySession:
        def rollback(self):
            pass

        def close(self):
            pass

    original_enabled = settings.intelligence_digest_enabled
    original_recipients = settings.intelligence_digest_recipients
    original_from = settings.alert_from_email
    original_host = settings.smtp_host
    settings.intelligence_digest_enabled = True
    settings.intelligence_digest_recipients = "ops@example.com"
    settings.alert_from_email = "alerts@example.com"
    settings.smtp_host = "smtp.example.com"

    monkeypatch.setattr(scheduler_module, "SessionLocal", lambda: DummySession())
    monkeypatch.setattr(
        scheduler_module,
        "_send_intelligence_digest",
        lambda db, dry_run=False: {
            "dry_run": dry_run,
            "recipient_count": 1,
            "recipients": ["ops@example.com"],
            "subject": "BagDrop intelligence brief",
            "brief_url": "https://bagdrop.xyz/intel",
            "arbitrage_count": 3,
            "new_drop_count": 2,
            "bag_index_count": 4,
        },
    )
    try:
        summary = await scheduler_module.run_intelligence_digest_job()
    finally:
        settings.intelligence_digest_enabled = original_enabled
        settings.intelligence_digest_recipients = original_recipients
        settings.alert_from_email = original_from
        settings.smtp_host = original_host

    assert summary["status"] == "sent"
    assert summary["recipient_count"] == 1


@pytest.mark.anyio
async def test_get_ops_summary_includes_retention_readiness():
    session = make_session()
    now = datetime.utcnow()
    session.add(
        WatchSubscription(
            email="buyer@example.com",
            brand="Hermès",
            model="Kelly Sellier 28",
            brand_slug="hermes",
            model_slug="kelly-sellier-28",
            source="market_page",
            is_active=True,
        )
    )
    session.flush()
    session.add(
        WatchAlertDelivery(
            watch_subscription_id=1,
            listing_id="fashionphile_1",
            email="buyer@example.com",
            created_at=now - timedelta(hours=2),
        )
    )
    session.commit()

    original_from = settings.alert_from_email
    original_host = settings.smtp_host
    original_watch_enabled = settings.watch_alert_scheduler_enabled
    original_digest_enabled = settings.intelligence_digest_enabled
    original_recipients = settings.intelligence_digest_recipients
    settings.alert_from_email = "alerts@example.com"
    settings.smtp_host = "smtp.example.com"
    settings.watch_alert_scheduler_enabled = True
    settings.intelligence_digest_enabled = True
    settings.intelligence_digest_recipients = "ops@example.com,ceo@example.com"
    try:
        summary = await get_ops_summary(session)
    finally:
        settings.alert_from_email = original_from
        settings.smtp_host = original_host
        settings.watch_alert_scheduler_enabled = original_watch_enabled
        settings.intelligence_digest_enabled = original_digest_enabled
        settings.intelligence_digest_recipients = original_recipients

    assert summary.active_watch_subscriptions == 1
    assert summary.watch_alert_deliveries_24h == 1
    assert summary.smtp_configured is True
    assert summary.watch_alert_scheduler_enabled is True
    assert summary.intelligence_digest_enabled is True
    assert summary.intelligence_digest_recipient_count == 2
