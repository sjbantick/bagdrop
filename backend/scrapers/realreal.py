"""The RealReal scraper — extracts from Next.js __NEXT_DATA__ or JSON API"""
import json
import re
from typing import Optional, List
from models import Platform
from scrapers.base import BaseScraper


class RealRealScraper(BaseScraper):
    platform = Platform.REALREAL
    base_url = "https://www.therealreal.com"

    # Sort by biggest price drops first
    SEARCH_URLS = [
        "/products?department=Women&category=Handbags&sort_by=price_drop_pct&page={page}",
        "/products?department=Women&category=Handbags&sort_by=sale_price_desc&page={page}",
    ]

    CONDITION_MAP = {
        "pristine": "pristine",
        "excellent": "excellent",
        "very good": "good",
        "good": "good",
        "fair": "fair",
    }

    def _extract_next_data(self, html: str) -> Optional[dict]:
        """Extract __NEXT_DATA__ JSON from Next.js page"""
        match = re.search(r'<script[^>]*id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
        if not match:
            return None
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            return None

    def _parse_condition(self, condition_str: str) -> str:
        if not condition_str:
            return "good"
        cond_lower = condition_str.lower()
        for key, val in self.CONDITION_MAP.items():
            if key in cond_lower:
                return val
        return "good"

    def _parse_products_from_next_data(self, data: dict) -> List[dict]:
        """Navigate Next.js page props to find product list"""
        try:
            # Try common paths in Next.js data structure
            props = data.get("props", {})
            page_props = props.get("pageProps", {})

            # Try various product list keys
            for key in ["products", "items", "listings", "results", "data"]:
                if key in page_props:
                    val = page_props[key]
                    if isinstance(val, list):
                        return val
                    if isinstance(val, dict) and "products" in val:
                        return val["products"]
                    if isinstance(val, dict) and "items" in val:
                        return val["items"]

            # Try nested structures
            for key in page_props:
                val = page_props[key]
                if isinstance(val, dict):
                    for subkey in ["products", "items", "listings"]:
                        if subkey in val and isinstance(val[subkey], list):
                            return val[subkey]
        except Exception:
            pass
        return []

    def _extract_listing_from_product(self, product: dict) -> Optional[dict]:
        """Extract listing fields from a RealReal product object"""
        try:
            # RealReal uses various field names
            product_id = (
                product.get("productId")
                or product.get("id")
                or product.get("slug")
                or product.get("handle")
            )
            if not product_id:
                return None

            # Price fields
            current_price = (
                product.get("price")
                or product.get("salePrice")
                or product.get("currentPrice")
                or product.get("priceAmount")
            )
            original_price = (
                product.get("originalPrice")
                or product.get("retailPrice")
                or product.get("compareAtPrice")
                or product.get("msrp")
            )

            if not current_price:
                return None

            # Handle price as string or dict
            if isinstance(current_price, dict):
                current_price = current_price.get("amount") or current_price.get("value")
            if isinstance(original_price, dict):
                original_price = original_price.get("amount") or original_price.get("value")

            current_price = float(str(current_price).replace(",", "").replace("$", ""))
            if original_price:
                original_price = float(str(original_price).replace(",", "").replace("$", ""))
            else:
                return None  # Skip if no original price

            if original_price <= current_price or current_price <= 0:
                return None

            brand = (
                product.get("brand")
                or product.get("designerName")
                or product.get("designer")
                or "Unknown"
            )
            if isinstance(brand, dict):
                brand = brand.get("name", "Unknown")

            model = (
                product.get("model")
                or product.get("name")
                or product.get("title")
                or product.get("shortDescription")
                or ""
            )
            size = product.get("size") or product.get("bagSize")
            color = product.get("color") or product.get("colorName")
            condition = product.get("condition") or product.get("conditionDescription") or ""

            slug = product.get("slug") or product.get("handle") or str(product_id)
            url = product.get("url") or f"{self.base_url}/products/{slug}"

            # Photo
            images = product.get("images") or product.get("photos") or []
            if isinstance(images, list) and images:
                first = images[0]
                photo_url = first if isinstance(first, str) else (
                    first.get("url") or first.get("src") or first.get("href")
                )
            else:
                photo_url = product.get("primaryImage") or product.get("image") or product.get("imageUrl")

            return {
                "platform_id": str(product_id),
                "brand": str(brand),
                "model": str(model),
                "url": str(url),
                "current_price": current_price,
                "original_price": original_price,
                "condition": self._parse_condition(str(condition)),
                "size": str(size) if size else None,
                "color": str(color) if color else None,
                "photo_url": str(photo_url) if photo_url else None,
            }
        except Exception as e:
            print(f"[RealReal] Error extracting product: {e}")
            return None

    async def _scrape_page(self, url: str) -> List[dict]:
        """Scrape a single search results page"""
        html = await self.fetch(url)
        if not html:
            return []

        next_data = self._extract_next_data(html)
        if not next_data:
            return []

        return self._parse_products_from_next_data(next_data)

    async def scrape(self) -> int:
        total_new = 0
        total_updated = 0
        total_found = 0
        max_pages = 20  # Cap at 20 pages to avoid overloading
        pages_with_products = 0

        for page in range(1, max_pages + 1):
            search_path = self.SEARCH_URLS[0].format(page=page)
            url = self.base_url + search_path

            products = await self._scrape_page(url)

            if not products:
                if page == 1:
                    self.fail_scrape(error="[RealReal] No products found on page 1 — site structure may have changed")
                break

            pages_with_products += 1

            for product in products:
                extracted = self._extract_listing_from_product(product)
                if not extracted:
                    continue

                total_found += 1
                is_new = self.save_listing(**extracted)
                if is_new:
                    total_new += 1
                else:
                    total_updated += 1

            # If we got fewer than expected, probably last page
            if len(products) < 10:
                break

        if pages_with_products > 0 and total_found == 0:
            self.fail_scrape(
                error="[RealReal] Parsed pages but extracted zero listings — source contract is broken",
                listings_found=0,
                listings_new=total_new,
                listings_updated=total_updated,
            )

        self.log_scrape(
            success=True,
            listings_found=total_found,
            listings_new=total_new,
            listings_updated=total_updated,
        )
        print(f"[RealReal] Done: {total_found} found, {total_new} new, {total_updated} updated")
        return total_new + total_updated
