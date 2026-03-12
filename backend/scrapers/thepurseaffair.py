"""The Purse Affair scraper — Shopify collection feed for pre-owned handbags."""
import json
import re
from typing import Optional

from models import Platform
from scrapers.base import BaseScraper


class ThePurseAffairScraper(BaseScraper):
    platform = Platform.THE_PURSE_AFFAIR
    base_url = "https://www.thepurseaffair.com"
    supports_full_inventory_tombstone = True
    collection = "handbags"

    SCORE_CONDITION_MAP = (
        (9.5, "pristine"),
        (8.8, "excellent"),
        (7.5, "good"),
        (0.0, "fair"),
    )

    def _normalize_tags(self, tags: list | str | None) -> list[str]:
        if isinstance(tags, list):
            return [str(tag).strip() for tag in tags if str(tag).strip()]
        if isinstance(tags, str):
            return [tag.strip() for tag in tags.split(",") if tag.strip()]
        return []

    def _parse_model_from_title(self, title: str, vendor: str) -> str:
        vendor_clean = vendor.strip()
        if title.lower().startswith(vendor_clean.lower()):
            title = title[len(vendor_clean):].strip()
        return title.strip()

    def _parse_condition(self, body_text: str) -> str:
        match = re.search(r"Condition:\s*([0-9]+(?:\.[0-9]+)?)\s*/\s*10", body_text, re.IGNORECASE)
        if match:
            score = float(match.group(1))
            for threshold, label in self.SCORE_CONDITION_MAP:
                if score >= threshold:
                    return label

        lowered = body_text.lower()
        if "immaculate" in lowered or "excellent condition" in lowered:
            return "excellent"
        if "great vintage condition" in lowered or "great condition" in lowered:
            return "good"
        return "good"

    def _parse_color(self, tags: list[str], body_text: str) -> Optional[str]:
        color_match = re.search(r"Colour:\s*([A-Za-z /-]+)", body_text, re.IGNORECASE)
        if color_match:
            return color_match.group(1).strip().title()

        for tag in tags:
            if re.fullmatch(r"[A-Za-z][A-Za-z -]{1,30}", tag) and tag.lower() not in {
                "available",
                "return",
                "shoulder",
                "crossbody",
                "clutch",
                "tote",
                "red",
            }:
                continue
        for tag in tags:
            lowered = tag.lower()
            if lowered in {"black", "white", "beige", "grey", "gray", "pink", "red", "blue", "brown", "green", "yellow", "orange", "purple", "silver", "gold", "ivory", "metallic", "tan", "cream", "navy"}:
                return tag.title()
        return None

    async def fetch_json(self, url: str) -> Optional[dict]:
        text = await self.fetch(url)
        if not text:
            return None
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return None

    async def scrape(self) -> int:
        total_new = 0
        total_updated = 0
        total_found = 0
        page = 1
        fetched_any_page = False
        self.begin_scrape_run()

        while True:
            url = f"{self.base_url}/collections/{self.collection}/products.json?limit=250&page={page}"
            data = await self.fetch_json(url)

            if not data or "products" not in data:
                break

            fetched_any_page = True
            products = data["products"]
            if not products:
                break

            for product in products:
                try:
                    variant = product.get("variants", [{}])[0] if product.get("variants") else {}
                    if not variant.get("available"):
                        continue

                    tags = self._normalize_tags(product.get("tags", []))
                    lowered_tags = {tag.lower() for tag in tags}
                    if "available" not in lowered_tags and "sold out" in lowered_tags:
                        continue

                    price_str = variant.get("price", "0") or "0"
                    compare_str = variant.get("compare_at_price")

                    if not compare_str:
                        continue

                    current_price = float(price_str)
                    original_price = float(compare_str)

                    if original_price <= current_price or current_price <= 0:
                        continue

                    vendor = product.get("vendor", "Unknown")
                    title = product.get("title", "")
                    handle = product.get("handle", "")
                    body_html = product.get("body_html", "")
                    body_text = re.sub(r"<[^>]+>", " ", body_html)

                    images = product.get("images", [])
                    photo_url = images[0]["src"] if images else None

                    platform_id = str(product.get("id", handle))
                    brand = self.normalize_brand(vendor)
                    model = self._parse_model_from_title(title, vendor)
                    condition = self._parse_condition(body_text)
                    color = self._parse_color(tags, body_text)
                    listing_url = f"{self.base_url}/products/{handle}"

                    total_found += 1
                    is_new = self.save_listing(
                        platform_id=platform_id,
                        brand=brand,
                        model=model,
                        url=listing_url,
                        current_price=current_price,
                        original_price=original_price,
                        condition=condition,
                        color=color,
                        photo_url=photo_url,
                        description=body_text[:500] if body_text else None,
                    )
                    self.track_seen_listing(platform_id)
                    if is_new:
                        total_new += 1
                    else:
                        total_updated += 1

                except Exception as e:
                    print(f"[ThePurseAffair] Error processing product: {e}")
                    continue

            if len(products) < 250:
                break

            page += 1

        if total_found == 0:
            self.fail_scrape(
                error="[ThePurseAffair] No qualifying bag listings found — source contract may have changed",
                listings_found=0,
                listings_new=0,
                listings_updated=0,
            )

        if not fetched_any_page:
            self.fail_scrape(
                error="[ThePurseAffair] Could not fetch products feed",
                listings_found=0,
                listings_new=0,
                listings_updated=0,
            )

        deactivated = self.deactivate_missing_listings()

        self.log_scrape(
            success=True,
            listings_found=total_found,
            listings_new=total_new,
            listings_updated=total_updated,
        )
        print(
            f"[ThePurseAffair] Done: {total_found} found, {total_new} new, "
            f"{total_updated} updated, {deactivated} deactivated"
        )
        return total_new + total_updated
