#!/usr/bin/env python3
"""Minimal BagDrop ops check against the public ops-summary endpoint."""

from __future__ import annotations

import argparse
import json
import sys
from urllib.error import HTTPError, URLError
from urllib.request import urlopen


def fetch_summary(url: str) -> dict:
    with urlopen(url, timeout=15) as response:
        return json.load(response)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check BagDrop scraper freshness and click activity via /api/admin/ops-summary."
    )
    parser.add_argument(
        "--url",
        default="http://localhost:8000/api/admin/ops-summary",
        help="Full ops summary endpoint URL.",
    )
    parser.add_argument(
        "--require-clicks",
        action="store_true",
        help="Fail when 24h outbound click volume is zero.",
    )
    args = parser.parse_args()

    try:
        summary = fetch_summary(args.url)
    except HTTPError as exc:
        print(f"ops check failed: HTTP {exc.code} from {args.url}", file=sys.stderr)
        return 2
    except URLError as exc:
        print(f"ops check failed: could not reach {args.url} ({exc.reason})", file=sys.stderr)
        return 2

    platforms = summary.get("platforms", [])
    stale = [platform for platform in platforms if platform.get("stale")]
    failed = [platform for platform in platforms if platform.get("last_run_success") is False]
    total_clicks = summary.get("total_outbound_clicks_24h", 0)

    print("BagDrop ops summary")
    print(f"- generated_at: {summary.get('generated_at')}")
    print(f"- stale_after_hours: {summary.get('stale_after_hours')}")
    print(f"- total_outbound_clicks_24h: {total_clicks}")

    for platform in platforms:
        name = platform.get("platform", "unknown")
        status = "stale" if platform.get("stale") else "fresh"
        last_run = platform.get("last_run_success")
        if last_run is True:
            last_run_label = "success"
        elif last_run is False:
            last_run_label = "failed"
        else:
            last_run_label = "unknown"

        print(
            f"- {name}: {status}, "
            f"last_run={last_run_label}, "
            f"active_listings={platform.get('active_listings', 0)}, "
            f"clicks_24h={platform.get('outbound_clicks_24h', 0)}"
        )

    if stale:
        print(
            "ops check failed: stale platforms -> "
            + ", ".join(platform.get("platform", "unknown") for platform in stale),
            file=sys.stderr,
        )
        return 1

    if failed:
        print(
            "ops check failed: latest run failed for -> "
            + ", ".join(platform.get("platform", "unknown") for platform in failed),
            file=sys.stderr,
        )
        return 1

    if args.require_clicks and total_clicks == 0:
        print("ops check failed: no outbound clicks recorded in the last 24h", file=sys.stderr)
        return 1

    print("ops check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
