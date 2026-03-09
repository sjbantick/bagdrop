"""Vestiaire Collective scraper — uses their catalog API"""
import json
import re
from typing import Optional, List
from models import Platform
from scrapers.base import BaseScraper


class VestiaireScraper(BaseScraper):
    platform = Platform.VESTIAIRE
    base_url = "https://www.vestiairecollective.com"
    api_base = "https://www.vestiairecollective.com"

    # Vestiaire women's bags search with price drop sort
    CATALOG_PATHS = [
        "/en-us/api/catalog/search?categoryId=296&page={page}&pageSize=48&sortBy=newlyAdded",
        "/en-us/handbags/?page={page}&sort=recently-added",
    ]

    CONDITION_MAP = {
        "never worn": "pristine",
        "pristine": "pristine",
        "like new": "excellent",
        "very good condition": "good",
        "good condition": "good",
        "fair condition": "fair",
    }

    def _parse_condition(self, condition_str: str) -> str:
        if not condition_str:
            return "good"
        cond_lower = condition_str.lower()
        for key, val in self.CONDITION_MAP.items():
            if key in cond_lower:
                return val
        return "good"

    def _extract_next_data(self, html: str) -> Optional[dict]:
        """Extract __NEXT_DATA__ or __NUXT__ data from page"""
        # Try Next.js
        match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if match:
            try:
                return {"type": "next", "data": json.loads(match.group(1))}
            except json.JSONDecodeError:
                pass

        # Try embedded JSON in window.__data__ or similar
        match = re.search(r'window\.__data__\s*=\s*(\{.*?\});', html, re.DOTALL)
        if match:
            try:
                return {"type": "window", "data": json.loads(match.group(1))}
            except json.JSONDecodeError:
                pass

        return None

    def _parse_products_from_page_data(self, page_data: dict) -> List[dict]:
        """Navigate page data structure to find product list"""
        data_type = page_data.get("type")
        data = page_data.get("data", {})

        if data_type == "next":
            try:
                props = data.get("props", {}).get("pageProps", {})
                for key in ["products", "items", "catalogue", "search", "results"]:
                    if key in props:
                        val = props[key]
                        if isinstance(val, list):
                            return val
                        if isinstance(val, dict):
                            for subkey in ["products", "items", "items_list", "results"]:
                                if subkey in val and isinstance(val[subkey], list):
                                    return val[subkey]
            except Exception:
                pass

        return []

    def _extract_listing(self, product: dict) -> Optional[dict]:
        """Extract listing fields from a Vestiaire product"""
        try:
            product_id = (
                product.get("id")
                or product.get("productId")
                or product.get("catalogProductId")
            )
            if not product_id:
                return None

            # Price — Vestiaire uses various formats
            price_obj = product.get("price") or product.get("priceInfo") or {}
            original_obj = product.get("originalPrice") or product.get("retailPrice") or {}

            if isinstance(price_obj, (int, float)):
                current_price = float(price_obj)
            elif isinstance(price_obj, dict):
                current_price = float(price_obj.get("cents", 0) / 100 or price_obj.get("amount", 0))
            elif isinstance(price_obj, str):
                current_price = float(re.sub(r"[^\d.]", "", price_obj) or 0)
            else:
                return None

            if isinstance(original_obj, (int, float)):
                original_price = float(original_obj)
            elif isinstance(original_obj, dict):
                original_price = float(original_obj.get("cents", 0) / 100 or original_obj.get("amount", 0))
            elif isinstance(original_obj, str):
                original_price = float(re.sub(r"[^\d.]", "", original_obj) or 0)
            else:
                original_price = 0

            if original_price <= current_price or current_price <= 0:
                return None  # Not a marked-down item

            # Brand
            brand_obj = product.get("brand") or product.get("designer") or {}
            if isinstance(brand_obj, dict):
                brand = brand_obj.get("name") or brand_obj.get("slug", "Unknown")
            else:
                brand = str(brand_obj) if brand_obj else "Unknown"

            # Model / name
            model = (
                product.get("name")
                or product.get("model")
                or product.get("title")
                or product.get("shortName")
                or ""
            )

            # Condition
            condition_raw = (
                product.get("condition")
                or product.get("conditionDescription")
                or product.get("item_condition")
                or ""
            )
            if isinstance(condition_raw, dict):
                condition_raw = condition_raw.get("label") or condition_raw.get("name") or ""

            # URL
            slug = product.get("link") or product.get("slug") or product.get("url") or str(product_id)
            if slug.startswith("http"):
                listing_url = slug
            else:
                listing_url = f"{self.base_url}{slug}" if slug.startswith("/") else f"{self.base_url}/{slug}"

            # Photo
            image = product.get("image") or product.get("photo") or product.get("thumbnail") or {}
            if isinstance(image, str):
                photo_url = image
            elif isinstance(image, dict):
                photo_url = image.get("url") or image.get("src") or image.get("medium")
            else:
                photo_url = None

            size = product.get("size") or product.get("bagSize")
            color = product.get("color") or product.get("colorName")

            return {
                "platform_id": str(product_id),
                "brand": str(brand),
                "model": str(model),
                "url": listing_url,
                "current_price": current_price,
                "original_price": original_price,
                "condition": self._parse_condition(str(condition_raw)),
                "size": str(size) if size else None,
                "color": str(color) if color else None,
                "photo_url": photo_url,
            }
        except Exception as e:
            print(f"[Vestiaire] Error extracting product: {e}")
            return None

    async def scrape(self) -> int:
        total_new = 0
        total_updated = 0
        total_found = 0
        max_pages = 15

        for page in range(1, max_pages + 1):
            # Try API endpoint first
            api_url = self.api_base + self.CATALOG_PATHS[0].format(page=page)
            text = await self.fetch(api_url)

            products = []

            if text:
                try:
                    data = json.loads(text)
                    # Try to extract products from JSON response
                    if isinstance(data, list):
                        products = data
                    elif isinstance(data, dict):
                        for key in ["products", "items", "results", "data", "catalogue"]:
                            if key in data and isinstance(data[key], list):
                                products = data[key]
                                break
                        if not products and "items" in data:
                            products = data.get("items", [])
                except json.JSONDecodeError:
                    # Fallback: parse HTML __NEXT_DATA__
                    page_url = self.base_url + self.CATALOG_PATHS[1].format(page=page)
                    html = await self.fetch(page_url)
                    if html:
                        page_data = self._extract_next_data(html)
                        if page_data:
                            products = self._parse_products_from_page_data(page_data)

            if not products:
                if page == 1:
                    print(f"[Vestiaire] No products found on page 1 — API may have changed")
                break

            for product in products:
                extracted = self._extract_listing(product)
                if not extracted:
                    continue

                total_found += 1
                is_new = self.save_listing(**extracted)
                if is_new:
                    total_new += 1
                else:
                    total_updated += 1

            if len(products) < 10:
                break

        self.log_scrape(
            success=True,
            listings_found=total_found,
            listings_new=total_new,
            listings_updated=total_updated,
        )
        print(f"[Vestiaire] Done: {total_found} found, {total_new} new, {total_updated} updated")
        return total_new + total_updated
