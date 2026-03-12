"""Shared text utilities for BagDrop."""
import re
import unicodedata


def slugify_text(value: str) -> str:
    """Convert display text into a URL-safe slug."""
    normalized = unicodedata.normalize("NFKD", value or "")
    ascii_value = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_value.lower()).strip("-")
    return slug or "market"


def market_path(brand: str, model: str) -> str:
    """Build a canonical market page path."""
    return f"/{slugify_text(brand)}/{slugify_text(model)}"
