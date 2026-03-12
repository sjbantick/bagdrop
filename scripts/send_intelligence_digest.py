#!/usr/bin/env python3
"""Send or preview the BagDrop intelligence digest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))

from database import SessionLocal, init_db  # noqa: E402
from digest import send_intelligence_digest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Send or preview the BagDrop intelligence digest.")
    parser.add_argument("--dry-run", action="store_true", help="Preview the digest without sending email.")
    args = parser.parse_args()

    init_db()
    db = SessionLocal()
    try:
        summary = send_intelligence_digest(db, dry_run=args.dry_run)
    finally:
        db.close()

    print(json.dumps(summary, indent=2))
    return 0



if __name__ == "__main__":
    raise SystemExit(main())
