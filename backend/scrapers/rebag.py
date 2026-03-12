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
    SUPPLEMENTAL_MAX_PAGES = 4
    SITEMAP_RECENT_COUNT = 6
    SITEMAP_HISTORICAL_COUNT = 6
    SITEMAP_RECENT_PRODUCT_LIMIT = 150
    SITEMAP_HISTORICAL_PRODUCT_LIMIT = 150
    SITEMAP_PRIORITY_PRODUCT_LIMIT = 120
    SITEMAP_PRIORITY_SITEMAP_LIMIT = 20
    SITEMAP_PRIORITY_PER_SITEMAP_LIMIT = 8
    PRIORITY_BRAND_KEYWORDS = [
        "chanel",
        "hermes",
        "louis-vuitton",
        "gucci",
        "celine",
        "prada",
        "dior",
        "bottega",
        "saint-laurent",
        "fendi",
    ]

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

    def _coerce_tags(self, tags: list | str | None) -> list[str]:
        if isinstance(tags, list):
            return [str(tag).strip() for tag in tags if str(tag).strip()]
        if isinstance(tags, str):
            return [tag.strip() for tag in tags.split(",") if tag.strip()]
        return []

    def _parse_condition(self, tags: list[str], variant_title: str) -> str:
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

    def _parse_color(self, tags: list[str]) -> Optional[str]:
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

    async def fetch_collection_page(self, collection: str, page: int) -> tuple[Optional[list[dict]], bool]:
        url = f"{self.base_url}/collections/{collection}/products.json?limit=250&page={page}"
        data = await self.fetch_json(url)
        if not data or "products" not in data:
            return None, True
        return data.get("products", []), False

    async def fetch_product_json(self, handle: str) -> Optional[dict]:
        data = await self.fetch_json(f"{self.base_url}/products/{handle}.json")
        if not data:
            return None
        return data.get("product")

    async def fetch_text(self, url: str) -> Optional[str]:
        return await self.fetch(url)

    def _extract_sitemap_urls(self, xml_text: str) -> list[str]:
        return re.findall(r"<loc>(.*?)</loc>", xml_text or "")

    def _extract_product_handles_from_sitemap(self, xml_text: str) -> list[str]:
        handles: list[str] = []
        for loc in self._extract_sitemap_urls(xml_text):
            match = re.search(r"/products/([^<]+?)(?:\.html)?$", loc)
            if match:
                handles.append(match.group(1))
        return handles

    def _select_historical_sitemaps(self, sitemap_urls: list[str]) -> list[str]:
        recent_count = max(self.SITEMAP_RECENT_COUNT, 0)
        if len(sitemap_urls) <= recent_count:
            return []

        older = sitemap_urls if recent_count == 0 else sitemap_urls[:-recent_count]
        if not older:
            return []

        count = min(self.SITEMAP_HISTORICAL_COUNT, len(older))
        if count <= 0:
            return []

        selected: list[str] = []
        seen: set[str] = set()
        if count == 1:
            candidate = older[0]
            selected.append(candidate)
            return selected

        max_index = len(older) - 1
        for position in range(count):
            index = round(position * max_index / (count - 1))
            candidate = older[index]
            if candidate in seen:
                continue
            selected.append(candidate)
            seen.add(candidate)
        return selected

    def _is_priority_handle(self, handle: str) -> bool:
        lowered = (handle or "").lower()
        return any(keyword in lowered for keyword in self.PRIORITY_BRAND_KEYWORDS)

    def _select_priority_sitemaps(self, sitemap_urls: list[str]) -> list[str]:
        limit = min(self.SITEMAP_PRIORITY_SITEMAP_LIMIT, len(sitemap_urls))
        if limit <= 0:
            return []

        selected: list[str] = []
        left = 0
        right = len(sitemap_urls) - 1
        take_from_right = True

        while left <= right and len(selected) < limit:
            if take_from_right:
                selected.append(sitemap_urls[right])
                right -= 1
            else:
                selected.append(sitemap_urls[left])
                left += 1
            take_from_right = not take_from_right

        return selected

    async def _hydrate_sitemap_handles(
        self,
        sitemap_urls: list[str],
        discovered_handles: set[str],
        limit: int,
        *,
        priority_only: bool = False,
        per_sitemap_limit: int | None = None,
    ) -> tuple[int, int, int]:
        total_found = 0
        total_new = 0
        total_updated = 0
        hydrated = 0

        for sitemap_url in sitemap_urls:
            sitemap_text = await self.fetch_text(sitemap_url)
            if not sitemap_text:
                continue

            handles = self._extract_product_handles_from_sitemap(sitemap_text)
            hydrated_this_sitemap = 0
            for handle in reversed(handles):
                if hydrated >= limit:
                    return total_found, total_new, total_updated
                if per_sitemap_limit is not None and hydrated_this_sitemap >= per_sitemap_limit:
                    break
                if not handle or handle in discovered_handles:
                    continue
                if priority_only and not self._is_priority_handle(handle):
                    continue

                discovered_handles.add(handle)
                hydrated += 1
                hydrated_this_sitemap += 1
                try:
                    product = await self.fetch_product_json(handle)
                    if not product:
                        continue
                    found, is_new = await self._process_product(product)
                    if not found:
                        continue
                    total_found += 1
                    if is_new:
                        total_new += 1
                    else:
                        total_updated += 1
                except Exception as e:
                    print(f"[Rebag] Error processing sitemap handle {handle}: {e}")
                    continue

        return total_found, total_new, total_updated

    def _is_bag_product(self, tags: list[str], title: str) -> bool:
        has_bag_tag = any(t in tags for t in ["handbag", "all-bags", "item-type-handbag"])
        lowered = title.lower()
        return has_bag_tag or "bag" in lowered or "clutch" in lowered

    def _extract_listing(self, product: dict) -> Optional[dict]:
        tags = self._coerce_tags(product.get("tags", []))
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

    async def _run_bulk_collection(self) -> tuple[int, int, int, set[str], bool]:
        total_found = 0
        total_new = 0
        total_updated = 0
        discovered_handles: set[str] = set()
        completed_inventory_pass = False

        for page in range(1, self.BULK_MAX_PAGES + 1):
            products, failed = await self.fetch_collection_page(self.BULK_COLLECTION, page)
            if failed:
                print(f"[Rebag] Bulk collection fetch failed on page {page}")
                break
            if not products:
                completed_inventory_pass = True
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
                completed_inventory_pass = True
                break

        return total_found, total_new, total_updated, discovered_handles, completed_inventory_pass

    async def _run_supplemental_collections(self, discovered_handles: set[str]) -> tuple[int, int, int, bool]:
        total_found = 0
        total_new = 0
        total_updated = 0
        failed = False

        for collection in self.SUPPLEMENTAL_COLLECTIONS:
            for page in range(1, self.SUPPLEMENTAL_MAX_PAGES + 1):
                products, page_failed = await self.fetch_collection_page(collection, page)
                if page_failed:
                    failed = True
                    print(f"[Rebag] Supplemental collection '{collection}' fetch failed on page {page}")
                    break
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

        return total_found, total_new, total_updated, failed

    async def _run_sitemap_discovery(self, discovered_handles: set[str]) -> tuple[int, int, int, bool]:
        total_found = 0
        total_new = 0
        total_updated = 0

        sitemap_index = await self.fetch_text(f"{self.base_url}/sitemap.xml")
        if not sitemap_index:
            return 0, 0, 0, True

        sitemap_urls = [
            url for url in self._extract_sitemap_urls(sitemap_index)
            if "sitemap_products_" in url
        ]
        if not sitemap_urls:
            return 0, 0, 0, True

        priority_sitemaps = self._select_priority_sitemaps(sitemap_urls)
        recent_sitemaps = list(reversed(sitemap_urls[-self.SITEMAP_RECENT_COUNT:]))
        historical_sitemaps = list(reversed(self._select_historical_sitemaps(sitemap_urls)))

        priority_found, priority_new, priority_updated = await self._hydrate_sitemap_handles(
            priority_sitemaps,
            discovered_handles,
            self.SITEMAP_PRIORITY_PRODUCT_LIMIT,
            priority_only=True,
            per_sitemap_limit=self.SITEMAP_PRIORITY_PER_SITEMAP_LIMIT,
        )
        total_found += priority_found
        total_new += priority_new
        total_updated += priority_updated

        recent_found, recent_new, recent_updated = await self._hydrate_sitemap_handles(
            recent_sitemaps,
            discovered_handles,
            self.SITEMAP_RECENT_PRODUCT_LIMIT,
        )
        total_found += recent_found
        total_new += recent_new
        total_updated += recent_updated

        historical_found, historical_new, historical_updated = await self._hydrate_sitemap_handles(
            historical_sitemaps,
            discovered_handles,
            self.SITEMAP_HISTORICAL_PRODUCT_LIMIT,
        )
        total_found += historical_found
        total_new += historical_new
        total_updated += historical_updated

        return total_found, total_new, total_updated, False

    async def scrape(self) -> int:
        self.begin_scrape_run()
        total_found, total_new, total_updated, discovered_handles, bulk_complete = await self._run_bulk_collection()
        supplemental_found, supplemental_new, supplemental_updated, supplemental_failed = await self._run_supplemental_collections(
            discovered_handles
        )
        total_found += supplemental_found
        total_new += supplemental_new
        total_updated += supplemental_updated
        sitemap_found, sitemap_new, sitemap_updated, sitemap_failed = await self._run_sitemap_discovery(
            discovered_handles
        )
        total_found += sitemap_found
        total_new += sitemap_new
        total_updated += sitemap_updated

        if sitemap_failed:
            print("[Rebag] Sitemap discovery failed or returned no sitemap index")

        if total_found == 0:
            self.fail_scrape(
                error="[Rebag] No qualifying listings found — fetch likely rate-limited or source contract changed",
                listings_found=0,
                listings_new=0,
                listings_updated=0,
            )

        deactivated = 0
        if bulk_complete and not supplemental_failed:
            deactivated = self.deactivate_missing_listings()
        else:
            print(
                "[Rebag] Skipping tombstone because the inventory pass was incomplete "
                f"(bulk_complete={bulk_complete}, supplemental_failed={supplemental_failed})"
            )

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
