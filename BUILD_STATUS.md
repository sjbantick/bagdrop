# BagDrop Build Status

## Current State

BagDrop is past the bare-MVP scaffold stage. The backend, scrapers, scheduler, feed UI, listing detail pages, and canonical brand/model market pages now exist in the repo and build successfully.

## Shipped

### Backend
- [x] FastAPI API with health check, listings feed, listing detail, price history, brands/models, new drops, bag index, stats, and admin scrape trigger
- [x] SQLAlchemy models for listings, price history, bag index snapshots, velocity scores, and scrape logs
- [x] Scheduler wiring for recurring scraper runs plus initial scrape on startup
- [x] Shared slug/canonical-path helpers for SEO market pages
- [x] Featured market endpoint: `GET /api/markets/featured`
- [x] Canonical market endpoint: `GET /api/markets/{brand_slug}/{model_slug}`
- [x] First-party outbound click tracking and redirect endpoint
- [x] Affiliate-ready outbound query templating with listing and surface placeholders
- [x] Ops summary endpoint for scraper freshness, last failures, and click activity
- [x] Top-click analytics endpoint for listings, markets, surfaces, and contexts

### Scrapers
- [x] Fashionphile scraper
- [x] Rebag scraper
- [x] The RealReal scraper
- [x] Vestiaire scraper

### Frontend
- [x] Main feed with filters, platform tabs, and live stats
- [x] Internal listing detail page at `/listings/[listingId]`
- [x] Canonical brand/model market pages at `/[brand]/[model]`
- [x] Featured markets section on the homepage
- [x] Price history chart component
- [x] Brand/model autocomplete in filters
- [x] `robots.txt` and dynamic sitemap
- [x] Sitemap now covers canonical market pages and listing detail pages from active inventory
- [x] Canonical metadata and generated OG images for homepage, market pages, and listing pages
- [x] Structured data on key owned surfaces: listings, markets, and `/intel`
- [x] Outbound marketplace CTAs routed through BagDrop tracking
- [x] Internal ops page at `/ops`
- [x] `/ops` top-click analytics for listings, markets, surfaces, and contexts
- [x] Arbitrage radar on the homepage using live market-average deltas
- [x] BagIndex board on the homepage using live brand-level price health
- [x] BagIndex scheduler persistence and trend deltas against stored history
- [x] New-drops radar on the homepage using a scored freshness signal
- [x] Shareable `/intel` page combining arbitrage, new drops, and BagIndex movers
- [x] SMTP-ready intelligence digest built from `/intel`
- [x] Scheduler-backed watchlist alert loop
- [x] Scheduler-backed intelligence digest loop
- [x] Market-page velocity score inferred from recent first-seen activity
- [x] Email watchlist capture on canonical market pages
- [x] SMTP-ready watchlist alert delivery loop with unsubscribe-safe links, freshness gating, and cooldowns
- [x] Production Next.js build passing

### Verification
- [x] `python3 -m pytest backend/tests/test_markets.py`
- [x] `python3 -m compileall backend`
- [x] `npm run build` in `frontend/`
- [x] `python3 scripts/check_ops.py --url ...` against a mock ops endpoint
- [x] GitHub Actions workflows added for CI and scheduled ops checks
- [x] GitHub Actions workflow added for Vercel frontend deployment
- [x] Launch checklist captured in `LAUNCH_CHECKLIST.md`

## Biggest Remaining Gaps

### Launch / Ops
1. Point `bagdrop.xyz` at the deployed frontend
2. Configure `BAGDROP_OPS_URL` in GitHub Actions once the backend URL is stable
3. Set `PUBLIC_API_URL`, `ALERT_FROM_EMAIL`, SMTP credentials, and scheduler env vars in production
4. Seed platform-specific affiliate params once accounts are ready
5. Let the scheduled `Ops Check` workflow monitor production and alert on stale/failed platforms

### Product
1. Seed live partner query templates on top of the tracked redirect path
2. Add throttling and stronger rules on top of the watchlist and intelligence digest loops
3. Add structured data and other SEO polish for owned surfaces

### SEO / Growth
1. Add editorial landing pages for top models and brands
2. Improve structured data once production URLs are fixed

## Recommended Next Move

The highest-value next step is the frontend/domain cutover. The backend is now live on Railway, the product has enough owned-page surface area to justify pushing it live and indexing it, and the repo has enough CI and scheduling scaffolding to support that launch.

Last updated: March 12, 2026
