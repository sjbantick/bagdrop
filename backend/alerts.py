"""Watchlist alert helpers for BagDrop."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from email.message import EmailMessage
import base64
import hashlib
import hmac
import smtplib
import ssl
from typing import Optional
from urllib.parse import urlencode

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from config import settings
from models import Listing, WatchAlertDelivery, WatchSubscription
from utils import market_path


@dataclass
class PendingWatchAlert:
    subscription: WatchSubscription
    listings: list[Listing]


def _sign_watch_payload(payload: str) -> str:
    signature = hmac.new(
        settings.watch_token_secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    return signature


def build_watch_unsubscribe_token(subscription: WatchSubscription) -> str:
    payload = f"{subscription.id}:{subscription.email}:{subscription.brand_slug}:{subscription.model_slug}"
    token = f"{payload}:{_sign_watch_payload(payload)}"
    return base64.urlsafe_b64encode(token.encode("utf-8")).decode("utf-8")


def resolve_watch_unsubscribe_token(token: str, db: Session) -> Optional[WatchSubscription]:
    try:
        decoded = base64.urlsafe_b64decode(token.encode("utf-8")).decode("utf-8")
        subscription_id, email, brand_slug, model_slug, signature = decoded.split(":", 4)
    except Exception:
        return None

    payload = f"{subscription_id}:{email}:{brand_slug}:{model_slug}"
    if not hmac.compare_digest(signature, _sign_watch_payload(payload)):
        return None

    return (
        db.query(WatchSubscription)
        .filter(
            and_(
                WatchSubscription.id == int(subscription_id),
                WatchSubscription.email == email,
                WatchSubscription.brand_slug == brand_slug,
                WatchSubscription.model_slug == model_slug,
            )
        )
        .first()
    )


def build_watch_unsubscribe_url(subscription: WatchSubscription) -> str:
    token = build_watch_unsubscribe_token(subscription)
    query = urlencode({"token": token})
    return f"{settings.public_api_url.rstrip('/')}/api/watchlists/unsubscribe?{query}"


def get_pending_watch_alerts(
    db: Session,
    limit_subscriptions: Optional[int] = None,
    per_subscription_limit: Optional[int] = None,
) -> list[PendingWatchAlert]:
    now = datetime.utcnow()
    freshness_cutoff = now - timedelta(hours=max(settings.watch_alert_freshness_hours, 1))
    effective_limit = per_subscription_limit or max(settings.watch_alert_max_listings, 1)
    query = (
        db.query(WatchSubscription)
        .filter(WatchSubscription.is_active == True)
        .order_by(WatchSubscription.created_at.asc())
    )

    if limit_subscriptions is not None:
        query = query.limit(limit_subscriptions)

    subscriptions = query.all()
    pending: list[PendingWatchAlert] = []

    for subscription in subscriptions:
        if (
            subscription.last_notified_at is not None
            and settings.watch_alert_cooldown_hours > 0
            and subscription.last_notified_at >= now - timedelta(hours=settings.watch_alert_cooldown_hours)
        ):
            continue

        delivered_listing_ids = (
            db.query(WatchAlertDelivery.listing_id)
            .filter(WatchAlertDelivery.watch_subscription_id == subscription.id)
            .all()
        )
        seen_listing_ids = [row[0] for row in delivered_listing_ids]
        listing_cutoff = max(subscription.created_at, freshness_cutoff)

        listings_query = (
            db.query(Listing)
            .filter(
                and_(
                    Listing.is_active == True,
                    Listing.brand == subscription.brand,
                    Listing.model == subscription.model,
                    Listing.first_seen >= listing_cutoff,
                )
            )
            .order_by(desc(Listing.first_seen), desc(Listing.drop_pct), Listing.current_price)
        )

        if seen_listing_ids:
            listings_query = listings_query.filter(~Listing.id.in_(seen_listing_ids))

        listings = listings_query.limit(effective_limit).all()
        if listings:
            pending.append(PendingWatchAlert(subscription=subscription, listings=listings))

    return pending


def render_watch_alert_email(subscription: WatchSubscription, listings: list[Listing]) -> tuple[str, str, str]:
    market_label = f"{subscription.brand} {subscription.model}"
    subject = f"BagDrop alert: {len(listings)} new {market_label} listings"
    market_url = f"{settings.public_app_url.rstrip('/')}{market_path(subscription.brand, subscription.model)}"
    unsubscribe_url = build_watch_unsubscribe_url(subscription)

    text_lines = [
        f"BagDrop found {len(listings)} new listings for {market_label}.",
        "",
        f"Open market page: {market_url}",
        "",
    ]

    for listing in listings:
        line = (
            f"- {listing.platform}: ${listing.current_price:,.0f}"
            f" | drop {listing.drop_pct or 0:.1f}%"
            f" | {listing.url}"
        )
        text_lines.append(line)

    text_lines.extend(["", f"Unsubscribe: {unsubscribe_url}"])

    html_items = "".join(
        [
            (
                "<li style=\"margin-bottom:14px;\">"
                f"<strong>{listing.platform}</strong> &middot; ${listing.current_price:,.0f}"
                f" &middot; drop {listing.drop_pct or 0:.1f}%"
                f"<br/><a href=\"{listing.url}\">Open marketplace listing</a>"
                "</li>"
            )
            for listing in listings
        ]
    )

    html = (
        "<div style=\"background:#050505;color:#ffffff;padding:24px;font-family:Arial,sans-serif;\">"
        f"<h1 style=\"font-size:28px;margin:0 0 12px;\">BagDrop alert: {market_label}</h1>"
        f"<p style=\"color:#d1d5db;line-height:1.6;\">We found {len(listings)} new listings for this market.</p>"
        f"<p><a href=\"{market_url}\" style=\"color:#f87171;\">Open the BagDrop market page</a></p>"
        f"<ul style=\"padding-left:18px;line-height:1.7;\">{html_items}</ul>"
        f"<p style=\"margin-top:24px;color:#9ca3af;\">Unsubscribe: <a href=\"{unsubscribe_url}\" style=\"color:#9ca3af;\">stop these alerts</a></p>"
        "</div>"
    )

    return subject, "\n".join(text_lines), html


def send_email_via_smtp(to_email: str, subject: str, text_body: str, html_body: str) -> None:
    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = settings.alert_from_email
    message["To"] = to_email
    if settings.alert_reply_to:
        message["Reply-To"] = settings.alert_reply_to

    message.set_content(text_body)
    message.add_alternative(html_body, subtype="html")

    if settings.smtp_use_ssl:
        with smtplib.SMTP_SSL(
            settings.smtp_host,
            settings.smtp_port,
            context=ssl.create_default_context(),
            timeout=30,
        ) as server:
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(message)
        return

    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
        if settings.smtp_use_tls:
            server.starttls(context=ssl.create_default_context())
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(message)


def deliver_watch_alerts(
    db: Session,
    *,
    dry_run: bool = False,
    limit_subscriptions: Optional[int] = None,
    per_subscription_limit: Optional[int] = None,
) -> dict:
    pending = get_pending_watch_alerts(
        db,
        limit_subscriptions=limit_subscriptions,
        per_subscription_limit=per_subscription_limit,
    )
    deliveries = []

    for item in pending:
        subject, text_body, html_body = render_watch_alert_email(item.subscription, item.listings)

        if not dry_run:
            if not settings.alert_from_email or not settings.smtp_host:
                raise RuntimeError("SMTP is not configured for watchlist alert delivery")

            try:
                send_email_via_smtp(item.subscription.email, subject, text_body, html_body)
            except smtplib.SMTPRecipientsRefused as exc:
                # Bad recipient address — skip this subscription, log, continue the batch
                print(f"[alerts] Skipping {item.subscription.email}: recipient refused ({exc})")
                continue
            except (smtplib.SMTPException, ssl.SSLError, OSError) as exc:
                # SMTP/TLS infrastructure failure — abort entire batch with context
                print(f"[alerts] SMTP failure delivering to {item.subscription.email}: {exc}")
                raise RuntimeError(f"SMTP delivery failed: {exc}") from exc

            now = datetime.utcnow()
            for listing in item.listings:
                db.add(
                    WatchAlertDelivery(
                        watch_subscription_id=item.subscription.id,
                        listing_id=listing.id,
                        email=item.subscription.email,
                    )
                )
            item.subscription.last_notified_at = now
            db.commit()

        deliveries.append(
            {
                "subscription_id": item.subscription.id,
                "email": item.subscription.email,
                "market": market_path(item.subscription.brand, item.subscription.model),
                "listing_count": len(item.listings),
                "subject": subject,
            }
        )

    return {
        "dry_run": dry_run,
        "subscriptions_with_alerts": len(deliveries),
        "deliveries": deliveries,
    }
