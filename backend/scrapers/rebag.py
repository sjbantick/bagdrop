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
    BULK_COLLECTION = "all"
    SUPPLEMENTAL_COLLECTIONS = [
        "all-bags",
        "new-arrivals",
        "chanel",
        "hermes",
        "louis-vuitton",
        "shoulder-bags",
        "cross-body-bags",
        "clutches",
        "unique-chanel-bags",
    ]
    BULK_MAX_PAGES = 60
    SUPPLEMENTAL_MAX_PAGES = 8

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

    async def fetch_collection_page(self, collection: str, page: int) -> list[dict]:
        url = f"{self.base_url}/collections/{collection}/products.json?limit=250&page={page}"
        data = await self.fetch_json(url)
        return data.get("products", []) if data else []

    async def fetch_product_json(self, handle: str) -> Optional[dict]:
        data = await self.fetch_json(f"{self.base_url}/products/{handle}.json")
        if not data:
            return None
        return data.get("product")

    def _is_bag_product(self, tags: list[str], title: str) -> bool:
        has_bag_tag = any(t in tags for t in ["handbag", "all-bags", "item-type-handbag"])
        lowered = title.lower()
        return has_bag_tag or "bag" in lowered or "clutch" in lowered

    def _extract_listing(self, product: dict) -> Optional[dict]:
        tags = product.get("tags", [])
        title = product.get("title", "")
        if not self._is_bag_product(tags, title):
            return None

        variant = product.get("variants", [{}])[0] if product.get("variants") else {}
        price_str = variant.get("price", "0") or "0"
        current_price = float(price_str)

        if current_price <= 0:
            return None

        body_html = product.get("body_html", "")
        original_price = self._parse_retail_price(body_html)
        if not original_price or original_price <= current_price:
            return None

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
        description = re.sub(r"<[^>]+>", "", body_html)[:500] if body_html else None

        return {
            "platform_id": platform_id,
            "brand": brand,
            "model": model,
            "url": listing_url,
            "current_price": current_price,
            "original_price": original_price,
            "condition": condition,
            "color": color,
            "photo_url": photo_url,
            "description": description,
        }

    def _save_extracted_listing(self, extracted: dict) -> bool:
        is_new = self.save_listing(**extracted)
        self.track_seen_listing(extracted["platform_id"])
        return is_new

    async def _process_product(self, product: dict) -> tuple[bool, bool]:
        extracted = self._extract_listing(product)
        if not extracted:
            return False, False
        is_new = self._save_extracted_listing(extracted)
        return True, is_new

    async def _run_bulk_collection(self) -> tuple[int, int, int, set[str]]:
        total_found = 0
        total_new = 0
        total_updated = 0
        discovered_handles: set[str] = set()

        for page in range(1, self.BULK_MAX_PAGES + 1):
            products = await self.fetch_collection_page(self.BULK_COLLECTION, page)
            if not products:
                break

            for product in products:
                handle = product.get("handle")
                if handle:
                    discovered_handles.add(handle)
                try:
                    found, is_new = await self._process_product(product)
                    if not found:
                        continue
                    total_found += 1
                    if is_new:
                        total_new += 1
                    else:
                        total_updated += 1
                except Exception as e:
                    print(f"[Rebag] Error processing bulk product: {e}")
                    continue

            if len(products) < 250:
                break

        return total_found, total_new, total_updated, discovered_handles

    async def _run_supplemental_collections(self, discovered_handles: set[str]) -> tuple[int, int, int]:
        total_found = 0
        total_new = 0
        total_updated = 0

        for collection in self.SUPPLEMENTAL_COLLECTIONS:
            for page in range(1, self.SUPPLEMENTAL_MAX_PAGES + 1):
                products = await self.fetch_collection_page(collection, page)
                if not products:
                    break

                for product in products:
                    handle = product.get("handle")
                    if not handle or handle in discovered_handles:
                        continue

                    discovered_handles.add(handle)
                    try:
                        hydrated = await self.fetch_product_json(handle)
                        if not hydrated:
                            continue
                        found, is_new = await self._process_product(hydrated)
                        if not found:
                            continue
                        total_found += 1
                        if is_new:
                            total_new += 1
                        else:
                            total_updated += 1
                    except Exception as e:
                        print(f"[Rebag] Error processing supplemental handle {handle}: {e}")
                        continue

                if len(products) < 250:
                    break

        return total_found, total_new, total_updated

    async def scrape(self) -> int:
        self.begin_scrape_run()
        total_found, total_new, total_updated, discovered_handles = await self._run_bulk_collection()
        supplemental_found, supplemental_new, supplemental_updated = await self._run_supplemental_collections(
            discovered_handles
        )
        total_found += supplemental_found
        total_new += supplemental_new
        total_updated += supplemental_updated

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
