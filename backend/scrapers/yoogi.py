"""Yoogi's Closet scraper — uses the public Algolia catalog index."""
import json
import re
import asyncio
from typing import Optional

from models import Platform
from scrapers.base import BaseScraper


class YoogiScraper(BaseScraper):
    platform = Platform.YOOGI
    base_url = "https://www.yoogiscloset.com"
    algolia_application_id = "MZKCR07F7K"
    algolia_api_key = "e2b1ab280e5418348458efe979ae441d"
    algolia_index = "magento2_yoogis_production_default_products_created_at_desc"

    CONDITION_MAP = {
        "new": "pristine",
        "new with tags": "pristine",
        "like new": "excellent",
        "excellent": "excellent",
        "gently used": "good",
        "very good": "good",
        "good": "good",
        "fair": "fair",
    }

    def _clean_text(self, value: Optional[str]) -> str:
        return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", value or "")).strip()

    def _parse_condition(self, value: Optional[str]) -> str:
        normalized = self._clean_text(value).lower()
        for key, mapped in sorted(self.CONDITION_MAP.items(), key=lambda item: len(item[0]), reverse=True):
            if key in normalized:
                return mapped
        return "good"

    def _extract_usd_amount(self, value) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            cleaned = re.sub(r"[^\d.]", "", value)
            return float(cleaned) if cleaned else None
        if isinstance(value, dict):
            if "USD" in value:
                result = self._extract_usd_amount(value["USD"])
                if result is not None:
                    return result
            for key in ["USD", "usd", "default", "final_price", "regular_price"]:
                if key in value:
                    result = self._extract_usd_amount(value[key])
                    if result is not None:
                        return result
            for nested in value.values():
                result = self._extract_usd_amount(nested)
                if result is not None:
                    return result
        return None

    def _extract_listing(self, hit: dict) -> Optional[dict]:
        url = hit.get("product_url") or hit.get("url")
        if not url:
            return None

        current_price = self._extract_usd_amount(
            hit.get("price")
            or hit.get("price_range", {}).get("minimum_price")
            or hit.get("price_range")
        )
        original_price = self._extract_usd_amount(
            hit.get("special_from_regular")
            or hit.get("regular_price")
            or hit.get("msrp")
            or hit.get("retail_price")
            or hit.get("price_range", {}).get("maximum_price")
        )

        if current_price is None or original_price is None:
            return None
        if current_price <= 0 or original_price <= current_price:
            return None

        brand = (
            hit.get("manufacturer")
            or hit.get("brand")
            or hit.get("brand_name")
            or "Unknown"
        )
        model = hit.get("name") or hit.get("title") or ""
        platform_id = str(hit.get("sku") or hit.get("objectID") or url.rstrip("/").split("/")[-1])
        photo_url = hit.get("image_url")
        if not photo_url:
            gallery = hit.get("media_gallery") or []
            if gallery and isinstance(gallery, list):
                photo_url = gallery[0]

        description_parts = []
        collection = self._clean_text(hit.get("collection") or hit.get("collection_name"))
        if collection:
            description_parts.append(collection)
        retail_price = self._extract_usd_amount(hit.get("retail_price") or hit.get("msrp"))
        if retail_price:
            description_parts.append(f"Retail Price: ${retail_price:,.0f}")

        return {
            "platform_id": platform_id,
            "brand": brand,
            "model": model,
            "url": url if url.startswith("http") else f"{self.base_url}{url}",
            "current_price": current_price,
            "original_price": original_price,
            "condition": self._parse_condition(hit.get("condition")),
            "photo_url": photo_url,
            "description": " | ".join(description_parts) if description_parts else None,
        }

    async def fetch_hits(self, page: int) -> Optional[dict]:
        endpoint = f"https://{self.algolia_application_id}-dsn.algolia.net/1/indexes/{self.algolia_index}/query"
        payload = {
            "params": (
                f"query=&hitsPerPage=1000&page={page}"
                "&filters=categories.level0:Handbags AND stock_qty=1"
            )
        }
        headers = self.get_headers()
        headers.update({
            "Content-Type": "application/json",
            "X-Algolia-Application-Id": self.algolia_application_id,
            "X-Algolia-API-Key": self.algolia_api_key,
            "Accept": "application/json",
        })

        for attempt in range(3):
            try:
                response = await self.http_client.post(
                    endpoint,
                    headers=headers,
                    content=json.dumps(payload),
                )
                if response.status_code == 200:
                    return response.json()
                print(f"[Yoogi] Algolia request failed: {response.status_code}")
            except Exception as exc:
                print(f"[Yoogi] Algolia request error (attempt {attempt + 1}): {exc}")
            if attempt < 2:
                await asyncio.sleep(2 ** attempt)
        return None

    async def scrape(self) -> int:
        total_new = 0
        total_updated = 0
        total_found = 0
        page = 0
        pages_with_hits = 0

        while True:
            data = await self.fetch_hits(page)
            if not data:
                if page == 0:
                    self.fail_scrape(error="[Yoogi] No Algolia data returned for page 0")
                break

            hits = data.get("hits") or []
            if not hits:
                if page == 0:
                    self.fail_scrape(error="[Yoogi] Algolia returned zero hits on page 0")
                break

            pages_with_hits += 1

            for hit in hits:
                try:
                    extracted = self._extract_listing(hit)
                    if not extracted:
                        continue
                    total_found += 1
                    is_new = self.save_listing(**extracted)
                    if is_new:
                        total_new += 1
                    else:
                        total_updated += 1
                except Exception as exc:
                    print(f"[Yoogi] Error processing hit: {exc}")
                    continue

            nb_pages = int(data.get("nbPages") or 0)
            page += 1
            if page >= nb_pages:
                break
            if page > 20:
                break

        if pages_with_hits > 0 and total_found == 0:
            self.fail_scrape(
                error="[Yoogi] Parsed Algolia hits but extracted zero discounted listings",
                listings_new=total_new,
                listings_updated=total_updated,
            )

        self.log_scrape(
            success=True,
            listings_found=total_found,
            listings_new=total_new,
            listings_updated=total_updated,
        )
        print(f"[Yoogi] Done: {total_found} found, {total_new} new, {total_updated} updated")
        return total_new + total_updated
