"""Rebag scraper — uses Shopify products.json at shop.rebag.com.

Rebag stores 'Estimated Retail Price' in body_html rather than compare_at_price.
Condition and color are encoded in product tags.
"""
import json
import re
from typing import Optional, Tuple
from models import Platform
from scrapers.base import BaseScraper


class RebagScraper(BaseScraper):
    platform = Platform.REBAG
    base_url = "https://shop.rebag.com"
    supports_full_inventory_tombstone = True

    # Condition map from Rebag tags/variant titles
    CONDITION_MAP = {
        "never worn": "pristine",
        "pristine": "pristine",
        "like new": "excellent",
        "excellent": "excellent",
        "great": "excellent",  # Rebag uses "Great" = our "excellent"
        "very good": "good",
        "good": "good",
        "fair": "fair",
    }

    def _parse_retail_price(self, body_html: str) -> Optional[float]:
        """Extract 'Estimated Retail Price: $X,XXX' from product description.
        HTML may contain tags between the label and the price value."""
        # Strip HTML tags first so we match plain text
        plain = re.sub(r"<[^>]+>", " ", body_html)
        match = re.search(r"Estimated Retail Price[^0-9]*([0-9,]+)", plain, re.IGNORECASE)
        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except ValueError:
                pass
        return None

    def _parse_condition(self, tags: list, variant_title: str) -> str:
        """Extract condition from tags or variant title"""
        # Check variant title first (e.g., "Very Good | Item # 414915/1 / White Gold")
        if variant_title:
            title_lower = variant_title.lower()
            for key, val in self.CONDITION_MAP.items():
                if title_lower.startswith(key):
                    return val

        # Check tags
        for tag in tags:
            tag_lower = tag.lower()
            for key, val in self.CONDITION_MAP.items():
                if tag_lower == key or tag_lower == key.replace(" ", "-"):
                    return val
        return "good"

    def _parse_color(self, tags: list) -> Optional[str]:
        """Extract color from exterior-color-* tags"""
        for tag in tags:
            if tag.startswith("exterior-color-"):
                color = tag.replace("exterior-color-", "").replace("-", " ").title()
                return color
        return None

    def _extract_brand_model(self, title: str, vendor: str) -> Tuple[str, str]:
        """Extract brand and model from Rebag title/vendor"""
        brand = self.normalize_brand(vendor) if vendor else "Unknown"
        # Rebag title is typically just the model name, vendor is the brand
        model = title.strip()
        return brand, model

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
        self.begin_scrape_run()

        # Rebag's /collections/all has all inventory; /new-arrivals for fresh stock
        # We use /all to get widest coverage
        while True:
            url = f"{self.base_url}/collections/all/products.json?limit=250&page={page}"
            data = await self.fetch_json(url)

            if not data or not data.get("products"):
                break

            products = data["products"]
            if not products:
                break

            for product in products:
                try:
                    # Skip non-bag items (jewelry, accessories, etc.)
                    tags = product.get("tags", [])
                    product_type = product.get("product_type", "").lower()
                    title = product.get("title", "")

                    # Only process handbags and wallets
                    has_bag_tag = any(t in tags for t in ["handbag", "all-bags", "item-type-handbag"])
                    if not has_bag_tag and "bag" not in title.lower() and "clutch" not in title.lower():
                        continue

                    variant = product.get("variants", [{}])[0] if product.get("variants") else {}
                    price_str = variant.get("price", "0") or "0"
                    current_price = float(price_str)

                    if current_price <= 0:
                        continue

                    # Get original/retail price from body_html
                    body_html = product.get("body_html", "")
                    original_price = self._parse_retail_price(body_html)

                    if not original_price or original_price <= current_price:
                        continue  # No discount to track

                    vendor = product.get("vendor", "Unknown")
                    handle = product.get("handle", "")
                    variant_title = variant.get("title", "")

                    images = product.get("images", [])
                    photo_url = images[0]["src"] if images else None

                    brand, model = self._extract_brand_model(title, vendor)
                    condition = self._parse_condition(tags, variant_title)
                    color = self._parse_color(tags)
                    platform_id = str(product.get("id", handle))
                    listing_url = f"{self.base_url}/products/{handle}"

                    # Clean description
                    description = re.sub(r"<[^>]+>", "", body_html)[:500] if body_html else None

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
                        description=description,
                    )
                    self.track_seen_listing(platform_id)
                    if is_new:
                        total_new += 1
                    else:
                        total_updated += 1

                except Exception as e:
                    print(f"[Rebag] Error processing product: {e}")
                    continue

            if len(products) < 250:
                break

            page += 1

        deactivated = self.deactivate_missing_listings()

        self.log_scrape(
            success=True,
            listings_found=total_found,
            listings_new=total_new,
            listings_updated=total_updated,
        )
        print(
            f"[Rebag] Done: {total_found} found, {total_new} new, "
            f"{total_updated} updated, {deactivated} deactivated"
        )
        return total_new + total_updated
