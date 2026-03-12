"""LuxeDH scraper — Shopify storefront fallback using products.json."""
import json
import re
from typing import Optional

from models import Platform
from scrapers.base import BaseScraper


class LuxeDHScraper(BaseScraper):
    platform = Platform.LUXEDH
    base_url = "https://www.luxedh.com"

    def _parse_condition(self, body_html: str, tags: list[str]) -> str:
        plain = re.sub(r"<[^>]+>", " ", body_html or "")
        for source in [plain, " ".join(tags)]:
            lowered = source.lower()
            if "pristine" in lowered or "new" in lowered:
                return "pristine"
            if "excellent" in lowered or "like new" in lowered:
                return "excellent"
            if "very good" in lowered or "good" in lowered:
                return "good"
            if "fair" in lowered:
                return "fair"
        return "good"

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
            data = await self.fetch_json(f"{self.base_url}/products.json?limit=250&page={page}")
            if not data or not data.get("products"):
                if page == 1:
                    self.fail_scrape(error="[LuxeDH] No products found on page 1 — feed unavailable or blocked")
                break

            for product in data["products"]:
                try:
                    variant = product.get("variants", [{}])[0] if product.get("variants") else {}
                    compare_str = variant.get("compare_at_price")
                    price_str = variant.get("price", "0") or "0"
                    if not compare_str:
                        continue

                    current_price = float(str(price_str).replace(",", ""))
                    original_price = float(str(compare_str).replace(",", ""))
                    if current_price <= 0 or original_price <= current_price:
                        continue

                    total_found += 1
                    is_new = self.save_listing(
                        platform_id=str(product.get("id", product.get("handle"))),
                        brand=product.get("vendor", "Unknown"),
                        model=product.get("title", ""),
                        url=f"{self.base_url}/products/{product.get('handle', '')}",
                        current_price=current_price,
                        original_price=original_price,
                        condition=self._parse_condition(product.get("body_html", ""), product.get("tags", [])),
                        photo_url=(product.get("images") or [{}])[0].get("src"),
                        description=re.sub(r"<[^>]+>", "", product.get("body_html", ""))[:500] or None,
                    )
                    if is_new:
                        total_new += 1
                    else:
                        total_updated += 1
                except Exception as exc:
                    print(f"[LuxeDH] Error processing product: {exc}")

            if len(data["products"]) < 250:
                break
            page += 1
            if page > 40:
                break

        if total_found == 0:
            self.fail_scrape(error="[LuxeDH] Parsed pages but extracted zero discounted listings")

        self.log_scrape(True, total_found, total_new, total_updated)
        print(f"[LuxeDH] Done: {total_found} found, {total_new} new, {total_updated} updated")
        return total_new + total_updated
