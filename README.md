# BagDrop — bagdrop.xyz

Real-time luxury handbag price drop tracker. Scans The RealReal, Vestiaire Collective, Fashionphile and Rebag to surface motivated sellers and buying opportunities.

## Getting Started

### Prerequisites
- Docker & Docker Compose (easiest)
- OR: Python 3.11+, Node.js 18+, PostgreSQL 15+, Redis 7+

### Quick Start (Docker)

```bash
# Clone and navigate to project
cd ~/Downloads/bagdrop

# Start all services
docker-compose up --build

# Backend runs on http://localhost:8000
# Frontend runs on http://localhost:3000
# API docs available at http://localhost:8000/docs
```

### Local Development (Without Docker)

**Backend:**
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Update config for local DB
# Edit config.py: DATABASE_URL = "sqlite:///./bagdrop.db"

python -m uvicorn main:app --reload
# API runs on http://localhost:8000
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
# Frontend runs on http://localhost:3000
```

## Architecture

### Backend (FastAPI)
- **models.py** — SQLAlchemy ORM models (Listing, PriceHistory, BagIndexSnapshot, etc.)
- **database.py** — Database connection and session management
- **config.py** — Configuration from environment variables
- **main.py** — FastAPI app with all API routes
- **scrapers/** — Platform-specific scrapers (RealReal, Vestiaire, Fashionphile, Rebag)

### Frontend (Next.js)
- **app/page.js** — Main listing feed view
- **app/listings/[listingId]/page.js** — Internal listing detail pages
- **app/[brand]/[model]/page.js** — Canonical SEO market pages
- **components/** — Reusable React components (Header, Filters, ListingCard)
- **Tailwind CSS** — Dark theme styling (matching panicselling.xyz aesthetic)

### Database Schema
- **listings** — Current active listings with metadata
- **price_history** — Immutable price log for each listing
- **bag_index_snapshots** — Weekly aggregate price health per brand
- **velocity_scores** — Relisting frequency scores
- **scrapes** — Scrape run logs

## API Endpoints

### GET /api/listings
Get listings with optional filters and sorting.
```bash
curl "http://localhost:8000/api/listings?brand=Hermès&sort_by=drop_pct&limit=50"
```

Query params:
- `brand` — Filter by brand name
- `model` — Filter by model name
- `platform` — Filter by platform (realreal, vestiaire, fashionphile, rebag)
- `min_drop_pct` / `max_drop_pct` — Filter by drop percentage
- `sort_by` — Sort by (drop_pct, drop_amount, current_price, last_seen)
- `limit` — Results per page (default 50, max 500)
- `offset` — Pagination offset

### GET /api/listings/{listing_id}
Get a specific listing

### GET /api/listings/{listing_id}/price-history
Get price history for a listing

### GET /api/brands
Get all unique brands

### GET /api/brands/{brand}/models
Get all models for a brand

### GET /api/new-drops
Get new price drops in the last N hours
```bash
curl "http://localhost:8000/api/new-drops?hours=24&limit=50"
```

### GET /api/opportunities/new-drops
Get high-signal fresh listings ranked by recency, markdown, and market context

### GET /api/intelligence/brief
Get a combined BagDrop intelligence payload for the shareable `/intel` brief page

### GET /api/bag-index
Get latest BagIndex snapshots (brand price health)

Supports live brand-level computation with trend deltas via `live=true` and persisted-history reads via `live=false`.

### GET /api/markets/featured
Get featured brand/model markets for homepage discovery and sitemap generation

### GET /api/markets/{brand_slug}/{model_slug}
Get the canonical BagDrop market page payload for a brand/model pair

### GET /api/opportunities/arbitrage
Get live listings priced materially below their brand/model market average across multiple platforms

### GET /api/markets/{brand_slug}/{model_slug}/velocity
Estimate market supply velocity from recent listing first-seen activity

### POST /api/admin/bag-index/recompute
Recompute current brand-level BagIndex values and optionally persist snapshots

### GET /api/listings/{listing_id}/outbound
Track a first-party outbound click, attach BagDrop attribution params, and redirect to the marketplace listing

### GET /api/admin/clicks/top
Get the top outbound-clicked listings, markets, surfaces, and contexts for monetization visibility

### GET /api/admin/ops-summary
Get scraper freshness, last run status, active listing counts, and outbound click activity by platform

### POST /api/watchlists
Capture email-based watch intent for a brand/model market

### GET /api/watchlists/unsubscribe
Deactivate a watch subscription from an email-safe token and redirect back to the canonical market page

### POST /api/admin/watchlists/send
Run the watchlist alert loop immediately (`dry_run=true` by default)

### POST /api/admin/scrape
Manually trigger a scrape (admin endpoint)

## Environment Variables

See `.env.example` for all options. Key variables:

```bash
# Database (PostgreSQL recommended for production)
DATABASE_URL=postgresql://user:password@localhost:5432/bagdrop

# Redis for caching
REDIS_URL=redis://localhost:6379/0

# Public app URL used for canonical links / redirects
PUBLIC_APP_URL=http://localhost:3000

# Public backend URL used in unsubscribe links and admin checks
PUBLIC_API_URL=http://localhost:8000

# Frontend canonical/OG base URL
NEXT_PUBLIC_SITE_URL=http://localhost:3000

# Outbound click attribution base
OUTBOUND_UTM_SOURCE=bagdrop

# Optional affiliate params appended on outbound redirect
# Supports placeholders like {{listing_id}}, {{platform}}, {{surface}}, {{brand_slug}}, {{model_slug}}, {{market_slug}}
REALREAL_AFFILIATE_QUERY=
VESTIAIRE_AFFILIATE_QUERY=
FASHIONPHILE_AFFILIATE_QUERY=
REBAG_AFFILIATE_QUERY

# Watchlist email alerting
WATCH_TOKEN_SECRET=bagdrop-dev-watch-secret
ALERT_FROM_EMAIL=
ALERT_REPLY_TO=
SMTP_HOST=
SMTP_PORT=587
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=true
SMTP_USE_SSL=false
WATCH_ALERT_MAX_LISTINGS=6
WATCH_ALERT_FRESHNESS_HOURS=168
WATCH_ALERT_COOLDOWN_HOURS=24

# Scraping behavior
SCRAPER_TIMEOUT=30  # Seconds per request
SCRAPER_RETRY_COUNT=3
SCRAPER_RATE_LIMIT_DELAY=1.0  # Seconds between requests

# Features
ENABLE_REALREAL=true
ENABLE_VESTIAIRE=true
ENABLE_FASHIONPHILE=true
ENABLE_REBAG=true
```

## Development

### Launch Checklist
Use [LAUNCH_CHECKLIST.md](/Users/sambantick/Downloads/bagdrop/LAUNCH_CHECKLIST.md) as the operating checklist for deployment, domain cutover, GitHub Actions configuration, and launch verification.

### Database Migrations
Currently using SQLAlchemy's automatic table creation. For production, set up Alembic:
```bash
alembic init alembic
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

### Running Tests
```bash
pytest backend/
```

### Ops Check
Use the lightweight monitoring script against a running BagDrop API:
```bash
python3 scripts/check_ops.py --url http://localhost:8000/api/admin/ops-summary
```

Fail if click volume is zero as well:
```bash
python3 scripts/check_ops.py --url http://localhost:8000/api/admin/ops-summary --require-clicks
```

### Watchlist Alerts
Preview the watchlist alert loop without sending email:
```bash
python3 scripts/send_watch_alerts.py --dry-run
```

Send real alerts once SMTP is configured:
```bash
python3 scripts/send_watch_alerts.py
```

### Intelligence Digest
Preview the `/intel` digest without sending email:
```bash
python3 scripts/send_intelligence_digest.py --dry-run
```

Send the digest once SMTP and `INTELLIGENCE_DIGEST_RECIPIENTS` are configured:
```bash
python3 scripts/send_intelligence_digest.py
```

The scheduler can also run both loops automatically in production:
- `WATCH_ALERT_SCHEDULER_ENABLED=true`
- `WATCH_ALERT_INTERVAL_MINUTES=30`
- `INTELLIGENCE_DIGEST_ENABLED=true`
- `INTELLIGENCE_DIGEST_HOUR_UTC=13`
- `INTELLIGENCE_DIGEST_MINUTE_UTC=0`

### GitHub Actions
The repo now includes two GitHub Actions workflows:

- `CI` runs backend tests, backend bytecode compilation, and the production frontend build on pushes to `main` and on pull requests.
- `Ops Check` runs every 6 hours and on demand. It uses the standard-library script above against a live deployment once `BAGDROP_OPS_URL` is configured in GitHub Actions secrets.

Frontend production deploys are handled by Vercel's native GitHub integration rather than GitHub Actions.

Recommended GitHub configuration after deployment:
```text
Secret: BAGDROP_OPS_URL=https://api.bagdrop.xyz/api/admin/ops-summary
Variable (optional): BAGDROP_REQUIRE_CLICKS=true
```

### Building for Production

**Backend:**
```bash
# Build image
docker build -t bagdrop-backend -f backend/Dockerfile .

# Push to registry
docker push your-registry/bagdrop-backend:latest
```

**Frontend:**
```bash
cd frontend
npm run build
npm start
```

## Features Implemented

### Data Infrastructure ✅
- [x] SQLAlchemy models (Listing, PriceHistory, BagIndex, VelocityScore)
- [x] FastAPI backend with CRUD endpoints
- [x] Database connection with PostgreSQL support
- [x] The RealReal scraper
- [x] Vestiaire Collective scraper
- [x] Fashionphile scraper
- [x] Rebag scraper
- [x] APScheduler cron job setup
- [x] Canonical market page API endpoints
- [x] Outbound click tracking and first-party redirect flow
- [x] Affiliate-ready outbound query templating with listing and surface placeholders
- [x] Ops summary endpoint for launch monitoring

### Web App ✅
- [x] Next.js project setup
- [x] Dark theme with Tailwind CSS
- [x] Listing feed component
- [x] Filter UI (brand, model, sort, drop %)
- [x] ListingCard component with price display
- [x] Internal listing detail pages
- [x] Canonical brand/model landing pages
- [x] Price history chart
- [x] Featured market discovery section
- [x] robots.txt and sitemap generation
- [x] Sitemap coverage for market pages and listing detail pages
- [x] Canonical metadata and generated OG images for homepage, market pages, and listing pages
- [x] Structured data on listing pages, market pages, and `/intel`
- [x] Tracked outbound marketplace links
- [x] Internal ops page at `/ops`
- [x] `/ops` top-click analytics for listings, markets, surfaces, and contexts
- [x] Homepage arbitrage radar powered by live market deltas
- [x] Homepage BagIndex board for brand-level price health
- [x] Scheduler-backed BagIndex snapshot persistence with same-day upsert behavior
- [x] Homepage new-drops radar with significance scoring
- [x] Shareable `/intel` intelligence brief page
- [x] SMTP-ready intelligence digest built from `/intel`
- [x] Scheduler-backed watchlist alert loop
- [x] Scheduler-backed intelligence digest loop
- [x] Market-page velocity scoring from recent supply pressure
- [x] Market-page watchlist capture
- [x] Unsubscribe-safe watchlist alert delivery loop
- [x] Search autocomplete for brands and models
- [x] GitHub Actions CI workflow
- [x] Scheduled GitHub Actions ops check scaffold
- [x] Backend deployed to Railway public URL
- [x] Frontend deploys through native Vercel GitHub integration
- [ ] Frontend domain cutover pending custom-domain access

### Price Intelligence ⏳
- [x] Cross-platform arbitrage detector
- [x] Velocity scoring system
- [x] BagIndex calculation
- [x] High-signal new-drops feed

### Growth & Distribution ⏳
- [x] SEO landing pages per brand/model
- [x] Watchlist email capture on canonical market pages
- [x] SMTP-based watchlist alert delivery loop
- [x] SMTP-ready intelligence digest
- [ ] More advanced digest / alert strategy
- [x] Shareable OG images for homepage, market pages, and listing pages
- [x] Dedicated OG image for `/intel`
- [x] Structured data for owned surfaces
- [ ] Content creator outreach list

### Monetization ⏳
- [ ] Affiliate links (RealReal, Vestiaire, etc.)
- [ ] Stripe premium alert subscription
- [ ] B2B reseller API

## Next Steps (Priority Order)

1. **Finish frontend/domain cutover** — Attach `bagdrop.xyz` in Vercel and remove the current SSO-protected alias bottleneck
2. **Configure production monitoring** — Set `BAGDROP_OPS_URL` and let the scheduled ops check watch the live stack
3. **Wire SMTP in production** — Set `PUBLIC_API_URL`, `ALERT_FROM_EMAIL`, SMTP credentials, and enable the scheduled alert/digest jobs
4. **Add affiliate parameters** — Seed live partner query templates on the tracked redirect flow
5. **Deepen retention/share loops** — Build digest and social flows on top of `/intel` and the intelligence stack
6. **Expand editorial SEO** — Brand/model pages beyond inventory-backed surfaces
7. **Premium alerts** — Monetization feature

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, Redis, Playwright, APScheduler
- **Frontend:** Next.js 14, React 18, Tailwind CSS
- **DevOps:** Docker, Docker Compose
- **Deployment:** Railway or Render

## Contributing

This is a solo project for now. Execution is tracked directly in the repo via `CEO_ROADMAP.md`, `BUILD_STATUS.md`, and `LAUNCH_CHECKLIST.md`.

## License

MIT — Build and share freely!

---

**Status:** Post-MVP launch preparation. Core product, tracked outbound flow, internal ops visibility, and CI scaffolding are in place; deployment remains the main blocker.
