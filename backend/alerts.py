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

        # If subscription has a target price, only include listings at or below it
        if subscription.target_price is not None:
            listings = [l for l in listings if l.current_price <= subscription.target_price]

        if listings:
            pending.append(PendingWatchAlert(subscription=subscription, listings=listings))

    return pending


def _listing_email_url(listing: Listing, surface: str = "watch_alert", context: str = "email") -> str:
    """Build a BagDrop outbound tracking URL for use inside emails.

    Routes clicks through /api/listings/{id}/outbound so affiliate UTMs and
    click-tracking fire before the redirect hits the marketplace.
    """
    base = settings.public_api_url.rstrip("/")
    return f"{base}/api/listings/{listing.id}/outbound?surface={surface}&context={context}"


def _platform_display_name(platform: str) -> str:
    return {
        "realreal": "The RealReal",
        "vestiaire": "Vestiaire",
        "fashionphile": "Fashionphile",
        "rebag": "Rebag",
    }.get(platform.lower(), platform.title())


def render_watch_alert_email(subscription: WatchSubscription, listings: list[Listing]) -> tuple[str, str, str]:
    market_label = f"{subscription.brand} {subscription.model}"
    count = len(listings)
    noun = "listing" if count == 1 else "listings"
    if subscription.target_price is not None:
        subject = f"BagDrop: {count} {market_label} {noun} under ${subscription.target_price:,.0f}"
    else:
        subject = f"BagDrop: {count} new {market_label} {noun} just dropped"
    market_url = f"{settings.public_app_url.rstrip('/')}{market_path(subscription.brand, subscription.model)}"
    unsubscribe_url = build_watch_unsubscribe_url(subscription)

    # ---- Plain-text body --------------------------------------------------
    text_lines = [
        f"BagDrop found {count} new {noun} for {market_label}.",
        "",
        f"Open market page: {market_url}",
        "",
    ]
    for listing in listings:
        tracked_url = _listing_email_url(listing)
        drop_str = f" | -{listing.drop_pct:.1f}% off" if listing.drop_pct else ""
        text_lines.append(
            f"- {_platform_display_name(listing.platform)}: ${listing.current_price:,.0f}{drop_str}"
            f" | {tracked_url}"
        )
    text_lines.extend(["", f"Unsubscribe: {unsubscribe_url}"])

    # ---- HTML body --------------------------------------------------------
    listing_rows = []
    for listing in listings:
        tracked_url = _listing_email_url(listing)
        platform_name = _platform_display_name(listing.platform)
        drop_badge = (
            f"<span style=\"display:inline-block;background:#ec4899;color:#fff;"
            f"border-radius:999px;padding:2px 10px;font-size:12px;font-weight:700;"
            f"letter-spacing:0.05em;margin-left:8px;\">-{listing.drop_pct:.1f}%</span>"
        ) if listing.drop_pct else ""
        condition_str = listing.condition.title() if listing.condition else ""
        listing_rows.append(
            f"<tr>"
            f"<td style=\"padding:14px 16px;border-bottom:1px solid #1f1f1f;\">"
            f"<div style=\"font-size:11px;text-transform:uppercase;letter-spacing:0.18em;"
            f"color:#9ca3af;margin-bottom:4px;\">{platform_name}</div>"
            f"<div style=\"font-size:22px;font-weight:700;color:#ffffff;\">"
            f"${listing.current_price:,.0f}{drop_badge}</div>"
            f"<div style=\"font-size:12px;color:#9ca3af;margin-top:4px;\">{condition_str}</div>"
            f"</td>"
            f"<td style=\"padding:14px 16px;border-bottom:1px solid #1f1f1f;"
            f"text-align:right;vertical-align:middle;\">"
            f"<a href=\"{tracked_url}\" style=\"display:inline-block;background:#ec4899;"
            f"color:#ffffff;text-decoration:none;border-radius:999px;padding:9px 20px;"
            f"font-size:13px;font-weight:600;\">View listing &rarr;</a>"
            f"</td>"
            f"</tr>"
        )

    rows_html = "\n".join(listing_rows)
    count_label = f"{count} new {noun}"

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#0a0a0a;font-family:Arial,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#0a0a0a;min-height:100vh;">
    <tr><td align="center" style="padding:32px 16px;">
      <table width="560" cellpadding="0" cellspacing="0" style="max-width:560px;width:100%;">
        <tr>
          <td style="padding-bottom:24px;">
            <a href="{settings.public_app_url}" style="text-decoration:none;">
              <span style="font-size:22px;font-weight:800;letter-spacing:-0.02em;color:#ffffff;">Bag</span><span style="font-size:22px;font-weight:800;letter-spacing:-0.02em;color:#ec4899;">Drop</span>
            </a>
          </td>
        </tr>
        <tr>
          <td style="background:#111111;border:1px solid #1f1f1f;border-radius:16px;padding:24px 24px 8px;">
            <p style="margin:0 0 4px;font-size:11px;text-transform:uppercase;letter-spacing:0.25em;color:#ec4899;">Watch Alert</p>
            <h1 style="margin:0 0 8px;font-size:26px;font-weight:700;color:#ffffff;line-height:1.2;">{market_label}</h1>
            <p style="margin:0 0 20px;font-size:15px;color:#9ca3af;line-height:1.6;">{count_label} just hit BagDrop.</p>
            <table width="100%" cellpadding="0" cellspacing="0">
              {rows_html}
            </table>
            <div style="padding:20px 0 8px;text-align:center;">
              <a href="{market_url}" style="display:inline-block;border:1px solid #374151;color:#d1d5db;text-decoration:none;border-radius:999px;padding:10px 24px;font-size:13px;">
                Open full market page
              </a>
            </div>
          </td>
        </tr>
        <tr>
          <td style="padding:24px 0 0;text-align:center;">
            <p style="margin:0;font-size:12px;color:#4b5563;line-height:1.7;">
              You&rsquo;re watching {market_label} on BagDrop.<br>
              <a href="{unsubscribe_url}" style="color:#6b7280;text-decoration:underline;">Unsubscribe from this market</a>
            </p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""

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
