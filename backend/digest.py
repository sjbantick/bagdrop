"""SMTP-ready intelligence digest built from the BagDrop brief."""
from __future__ import annotations

from typing import Iterable, List

from alerts import send_email_via_smtp
from config import settings
from main import _build_intelligence_brief


def parse_digest_recipients(raw: str | None = None) -> List[str]:
    value = raw if raw is not None else settings.intelligence_digest_recipients
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def render_intelligence_digest(brief) -> tuple[str, str, str]:
    intel_url = f"{settings.public_app_url.rstrip('/')}/intel"
    subject = "BagDrop intelligence brief"

    text_lines = [
        "BagDrop intelligence brief",
        "",
        f"Open brief: {intel_url}",
        "",
        f"Arbitrage ideas: {len(brief.arbitrage)}",
        f"New drops: {len(brief.new_drops)}",
        f"BagIndex movers: {len(brief.bag_index_movers)}",
    ]

    if brief.arbitrage:
        text_lines.extend(["", "Top arbitrage"])
        for item in brief.arbitrage[:3]:
            text_lines.append(
                f"- {item.listing.brand} {item.listing.model} on {item.listing.platform}: "
                f"${item.listing.current_price:,.0f} ({item.market_gap_pct:.1f}% below market)"
            )

    if brief.new_drops:
        text_lines.extend(["", "Top new drops"])
        for item in brief.new_drops[:3]:
            text_lines.append(
                f"- {item.listing.brand} {item.listing.model}: "
                f"score {item.significance_score:.1f}, age {item.hours_since_first_seen:.1f}h"
            )

    html = (
        "<div style=\"background:#050505;color:#ffffff;padding:24px;font-family:Arial,sans-serif;\">"
        "<h1 style=\"font-size:28px;margin:0 0 12px;\">BagDrop intelligence brief</h1>"
        "<p style=\"color:#d1d5db;line-height:1.6;\">A combined read on arbitrage, new drops, and brand-level price health.</p>"
        f"<p><a href=\"{intel_url}\" style=\"color:#f87171;\">Open the full brief</a></p>"
        f"<p style=\"color:#9ca3af;\">Arbitrage ideas: {len(brief.arbitrage)} &middot; "
        f"New drops: {len(brief.new_drops)} &middot; "
        f"BagIndex movers: {len(brief.bag_index_movers)}</p>"
        "</div>"
    )

    return subject, "\n".join(text_lines), html


def send_intelligence_digest(db, *, dry_run: bool = False) -> dict:
    recipients = parse_digest_recipients()
    brief = _build_intelligence_brief(db)
    subject, text_body, html_body = render_intelligence_digest(brief)

    if not dry_run:
        if not recipients:
            raise RuntimeError("INTELLIGENCE_DIGEST_RECIPIENTS is not configured")
        if not settings.alert_from_email or not settings.smtp_host:
            raise RuntimeError("SMTP is not configured for intelligence digest delivery")
        for recipient in recipients:
            send_email_via_smtp(recipient, subject, text_body, html_body)

    return {
        "dry_run": dry_run,
        "recipient_count": len(recipients),
        "recipients": recipients,
        "subject": subject,
        "brief_url": f"{settings.public_app_url.rstrip('/')}/intel",
        "arbitrage_count": len(brief.arbitrage),
        "new_drop_count": len(brief.new_drops),
        "bag_index_count": len(brief.bag_index_movers),
    }
