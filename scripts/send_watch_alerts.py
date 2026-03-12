#!/usr/bin/env python3
"""Send or preview BagDrop watchlist alerts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from alerts import deliver_watch_alerts  # noqa: E402
from database import SessionLocal, init_db  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Send or preview BagDrop watchlist alerts.")
    parser.add_argument("--dry-run", action="store_true", help="Preview alerts without sending email.")
    parser.add_argument("--limit-subscriptions", type=int, default=None, help="Limit subscriptions processed.")
    parser.add_argument("--per-subscription-limit", type=int, default=6, help="Max listings per watch email.")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        summary = deliver_watch_alerts(
            db,
            dry_run=args.dry_run,
            limit_subscriptions=args.limit_subscriptions,
            per_subscription_limit=args.per_subscription_limit,
        )
    finally:
        db.close()

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
