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

### GET /api/bag-index
Get latest BagIndex snapshots (brand price health)

### POST /api/admin/scrape
Manually trigger a scrape (admin endpoint)

## Environment Variables

See `.env.example` for all options. Key variables:

```bash
# Database (PostgreSQL recommended for production)
DATABASE_URL=postgresql://user:password@localhost:5432/bagdrop

# Redis for caching
REDIS_URL=redis://localhost:6379/0

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
- [ ] The RealReal scraper (in progress)
- [ ] Vestiaire Collective scraper (pending)
- [ ] Fashionphile scraper (pending)
- [ ] Rebag scraper (pending)
- [ ] Price drop detection engine (pending)
- [ ] APScheduler cron job setup (pending)

### Web App ✅
- [x] Next.js project setup
- [x] Dark theme with Tailwind CSS
- [x] Listing feed component
- [x] Filter UI (brand, model, sort, drop %)
- [x] ListingCard component with price display
- [ ] Price history chart (pending)
- [ ] Search autocomplete (pending)
- [ ] Deploy to Railway (pending)

### Price Intelligence ⏳
- [ ] Cross-platform arbitrage detector
- [ ] Velocity scoring system
- [ ] BagIndex calculation
- [ ] "New Drops" alert feed

### Growth & Distribution ⏳
- [ ] SEO landing pages per brand/model
- [ ] Weekly email digest
- [ ] Shareable drop cards (OG image generation)
- [ ] Content creator outreach list

### Monetization ⏳
- [ ] Affiliate links (RealReal, Vestiaire, etc.)
- [ ] Stripe premium alert subscription
- [ ] B2B reseller API

## Next Steps (Priority Order)

1. **Implement The RealReal scraper** — Start with the largest/most popular platform
2. **Build price drop detection** — Core feature that powers everything
3. **Deploy MVP to Railway** — Get it live at bagdrop.xyz
4. **Add more scrapers** — Vestiaire, Fashionphile, Rebag
5. **Launch email digest** — Primary retention mechanism
6. **SEO landing pages** — Drive organic traffic from bag searches
7. **Premium alerts** — Monetization feature

## Tech Stack

- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, Redis, Playwright, APScheduler
- **Frontend:** Next.js 14, React 18, Tailwind CSS
- **DevOps:** Docker, Docker Compose
- **Deployment:** Railway or Render

## Contributing

This is a solo project for now. All tasks tracked in Paperclip.

## License

MIT — Build and share freely!

---

**Status:** MVP in development. Core backend infrastructure complete. Frontend ready for first scraper integration.
