"""Fashionphile scraper — uses Shopify products.json API"""
import json
import re
from typing import Optional
from models import Platform
from scrapers.base import BaseScraper


class FashionphileScraper(BaseScraper):
    platform = Platform.FASHIONPHILE
    base_url = "https://fashionphile.com"

    CONDITION_MAP = {
        "never worn": "pristine",
        "pristine": "pristine",
        "like new": "excellent",
        "excellent": "excellent",
        "very good": "good",
        "good": "good",
        "fair": "fair",
        "poor": "fair",
    }

    def _parse_condition(self, tags: list) -> str:
        for tag in tags:
            tag_lower = tag.lower()
            for key, val in self.CONDITION_MAP.items():
                if key in tag_lower:
                    return val
        return "good"

    def _parse_model_from_title(self, title: str, vendor: str) -> str:
        """Strip vendor prefix from title to get model name"""
        vendor_clean = vendor.strip()
        if title.lower().startswith(vendor_clean.lower()):
            title = title[len(vendor_clean):].strip()
        return title.strip()

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

        while True:
            url = f"{self.base_url}/collections/handbags/products.json?limit=250&page={page}"
            data = await self.fetch_json(url)

            if not data or not data.get("products"):
                break

            products = data["products"]
            if not products:
                break

            for product in products:
                try:
                    variant = product.get("variants", [{}])[0] if product.get("variants") else {}
                    price_str = variant.get("price", "0") or "0"
                    compare_str = variant.get("compare_at_price")

                    if not compare_str:
                        continue  # No original price, no drop to track

                    current_price = float(price_str)
                    original_price = float(compare_str)

                    if original_price <= current_price or current_price <= 0:
                        continue  # Not a real drop

                    vendor = product.get("vendor", "Unknown")
                    title = product.get("title", "")
                    handle = product.get("handle", "")
                    tags = product.get("tags", [])
                    body_html = product.get("body_html", "")

                    images = product.get("images", [])
                    photo_url = images[0]["src"] if images else None

                    brand = self.normalize_brand(vendor)
                    model = self._parse_model_from_title(title, vendor)
                    condition = self._parse_condition(tags)
                    platform_id = str(product.get("id", handle))
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
                        photo_url=photo_url,
                        description=re.sub(r"<[^>]+>", "", body_html)[:500] if body_html else None,
                    )
                    if is_new:
                        total_new += 1
                    else:
                        total_updated += 1

                except Exception as e:
                    print(f"[Fashionphile] Error processing product: {e}")
                    continue

            if len(products) < 250:
                break  # Last page

            page += 1

        self.log_scrape(
            success=True,
            listings_found=total_found,
            listings_new=total_new,
            listings_updated=total_updated,
        )
        print(f"[Fashionphile] Done: {total_found} found, {total_new} new, {total_updated} updated")
        return total_new + total_updated
