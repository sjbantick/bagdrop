"""Vestiaire Collective scraper — uses their catalog API"""
import asyncio
import json
import re
from typing import Optional, List
from models import Platform
from scrapers.base import BaseScraper


class VestiaireScraper(BaseScraper):
    platform = Platform.VESTIAIRE
    base_url = "https://us.vestiairecollective.com"
    api_base = "https://www.vestiairecollective.com"
    image_base = "https://images.vestiairecollective.com"
    browser_search_base = "https://us.vestiairecollective.com/women-bags/handbags/?page={page}"
    browser_api_url = "https://search.vestiairecollective.com/v1/product/search"

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
            if not original_obj:
                discount = product.get("discount") or {}
                if isinstance(discount, dict):
                    original_obj = discount.get("originalPrice") or {}

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
            if isinstance(model, dict):
                model = model.get("name") or model.get("label") or ""

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
            image = product.get("image") or product.get("photo") or product.get("thumbnail")
            if isinstance(image, str):
                photo_url = image
            elif isinstance(image, dict):
                photo_url = image.get("url") or image.get("src") or image.get("medium")
            else:
                pictures = product.get("pictures") or []
                if pictures:
                    first_picture = pictures[0]
                    if isinstance(first_picture, str):
                        photo_url = (
                            f"{self.image_base}{first_picture}"
                            if first_picture.startswith("/")
                            else first_picture
                        )
                    else:
                        photo_url = None
                else:
                    photo_url = None

            size = product.get("size") or product.get("bagSize")
            if isinstance(size, dict):
                size = size.get("name") or size.get("label")

            color = product.get("color") or product.get("colorName")
            if not color:
                colors = product.get("colors") or {}
                if isinstance(colors, dict):
                    all_colors = colors.get("all") or []
                    if all_colors:
                        first_color = all_colors[0]
                        color = first_color.get("name") if isinstance(first_color, dict) else first_color

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

    async def _scrape_page_with_browser(self, page_num: int) -> List[dict]:
        try:
            from playwright.async_api import async_playwright
        except Exception as e:
            print(f"[Vestiaire] Playwright unavailable: {e}")
            return []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=True,
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--no-sandbox",
                        "--disable-dev-shm-usage",
                    ],
                )
                context = await browser.new_context(
                    user_agent=self.get_headers()["User-Agent"],
                    locale="en-US",
                    viewport={"width": 1440, "height": 1800},
                )
                page = await context.new_page()

                async with page.expect_response(
                    lambda response: response.url.startswith(self.browser_api_url),
                    timeout=max(self.http_client.timeout.connect * 1000, 30000),
                ) as response_info:
                    await page.goto(
                        self.browser_search_base.format(page=page_num),
                        wait_until="domcontentloaded",
                        timeout=max(self.http_client.timeout.connect * 1000, 30000),
                    )

                response = await response_info.value
                data = await response.json()
                products = data.get("items", [])
                await context.close()
                await browser.close()
                return products
        except Exception as e:
            print(f"[Vestiaire] Browser scrape failed on page {page_num}: {repr(e)}")
            return []

    async def scrape(self) -> int:
        total_new = 0
        total_updated = 0
        total_found = 0
        max_pages = 10
        pages_with_products = 0

        for page in range(1, max_pages + 1):
            products = await self._scrape_page_with_browser(page)

            if not products:
                if page == 1:
                    self.fail_scrape(error="[Vestiaire] No products found on page 1 — browser-backed search is blocked")
                break

            pages_with_products += 1

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

        if pages_with_products > 0 and total_found == 0:
            self.fail_scrape(
                error="[Vestiaire] Parsed pages but extracted zero listings — source contract is broken",
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
        print(f"[Vestiaire] Done: {total_found} found, {total_new} new, {total_updated} updated")
        return total_new + total_updated
