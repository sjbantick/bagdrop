# BagDrop Build Status

## ✅ Complete (MVP Foundation Ready)

### Backend Infrastructure
- [x] FastAPI server with CORS
- [x] SQLAlchemy ORM models (Listing, PriceHistory, BagIndexSnapshot, VelocityScore, Scrape)
- [x] PostgreSQL + SQLite support
- [x] Database connection pooling
- [x] Configuration system (environment variables)
- [x] Base scraper class with retry logic, rate limiting, user agent rotation

### API Endpoints (Ready)
- [x] GET /api/listings — Filterable, sortable listing feed
- [x] GET /api/listings/{id} — Single listing details
- [x] GET /api/listings/{id}/price-history — Price history chart data
- [x] GET /api/brands — Brand autocomplete
- [x] GET /api/brands/{brand}/models — Model autocomplete
- [x] GET /api/new-drops — Last 24h price drops (news feed)
- [x] GET /api/bag-index — Brand health snapshots
- [x] POST /api/admin/scrape — Manual trigger
- [x] Interactive docs at /docs (Swagger UI)

### Frontend (Next.js 14)
- [x] Dark theme (black background, red accents, gray borders)
- [x] Tailwind CSS configured
- [x] Header component with BagDrop branding
- [x] Listing card component (image placeholder, price, drop %, platform badge)
- [x] Filter UI (brand, model, sort by, min drop %)
- [x] Main feed page pulling from backend API
- [x] Responsive grid layout (mobile, tablet, desktop)
- [x] Hover effects and interactive elements

### Project Setup
- [x] Docker Compose for local development
- [x] Backend Dockerfile
- [x] Frontend Dockerfile
- [x] .env.example with all configuration options
- [x] .gitignore
- [x] requirements.txt (Python dependencies)
- [x] package.json (Node dependencies)
- [x] Comprehensive README
- [x] CLAUDE.md (project brief)

---

## ⏳ Next (Priority Order)

### Phase 1: First Scraper (Day 1-2)
1. **Implement The RealReal scraper** (`backend/scrapers/realreal.py`)
   - Parse HTML/API to extract listings
   - Extract: brand, model, size, color, condition, price, photos
   - Normalize brand/model names
   - Save to database via `save_listing()`

2. **Test scraper locally**
   ```bash
   python backend/scrapers/realreal.py --test
   ```

3. **Wire up APScheduler** (`backend/scheduler.py`)
   - Run scraper every 4 hours
   - Log runs to database
   - Handle failures gracefully

### Phase 2: Deploy MVP (Day 3)
1. Set up Railway or Render account
2. Push code to GitHub
3. Configure PostgreSQL on Railway
4. Configure Redis on Railway
5. Deploy backend → `https://bagdrop-api.railway.app`
6. Deploy frontend → `https://bagdrop.xyz`
7. Update NEXT_PUBLIC_API_URL in frontend

### Phase 3: More Scrapers (Day 4-5)
1. Vestiaire Collective scraper
2. Fashionphile scraper
3. Rebag scraper
4. Verify data quality across all platforms

### Phase 4: Intelligence Features (Day 6-7)
1. **Price drop detection** — Flag >10% drops
2. **Cross-platform arbitrage** — Same bag, different prices
3. **Velocity scoring** — Relisting frequency = distress signal
4. **BagIndex** — Weekly aggregate price health per brand

### Phase 5: Growth (Week 2)
1. **SEO landing pages** — `/chanel/classic-flap`, etc.
2. **Email digest** — Weekly top 10 drops
3. **Social share cards** — OG image generation per listing
4. **Outreach** — Contact 50 bag investment YouTubers/TikTokers

### Phase 6: Monetization (Week 2-3)
1. **Affiliate links** — RealReal, Vestiaire, Fashionphile, Rebag
2. **Premium alerts** — Stripe subscription ($9/mo for custom watchlists)
3. **B2B API** — Data access for resellers ($99/mo)

---

## Quick Start

```bash
# Install dependencies
cd ~/Downloads/bagdrop
docker-compose up --build

# In another terminal, once backend is running:
# Create first listing manually to test
curl -X POST http://localhost:8000/api/admin/seed

# View at http://localhost:3000
```

---

## Tech Stack Summary
- **Backend:** FastAPI, SQLAlchemy, PostgreSQL, Redis, Playwright/httpx, APScheduler
- **Frontend:** Next.js 14, React 18, Tailwind CSS
- **Deployment:** Docker → Railway/Render
- **Domain:** bagdrop.xyz (not yet registered/deployed)

---

## Key Decisions
1. **SQLite for dev, PostgreSQL for prod** — Easy local development
2. **FastAPI** — Modern, fast, auto docs
3. **Next.js** — Best-in-class React framework
4. **Dark theme** — Matches panicselling.xyz aesthetic, fits luxury/urgency
5. **No auth yet** — MVP is public, premium features later
6. **CSV/JSON exports** — No B2B API until after MVP

---

## File Structure
```
bagdrop/
├── CLAUDE.md
├── README.md
├── BUILD_STATUS.md (this file)
├── .env.example
├── .gitignore
├── docker-compose.yml
├── backend/
│   ├── requirements.txt
│   ├── Dockerfile
│   ├── config.py
│   ├── database.py
│   ├── models.py
│   ├── main.py
│   └── scrapers/
│       ├── __init__.py
│       └── base.py
├── frontend/
│   ├── package.json
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── Dockerfile
│   ├── app/
│   │   ├── layout.js
│   │   ├── page.js
│   │   └── globals.css
│   └── components/
│       ├── Header.js
│       ├── Filters.js
│       └── ListingCard.js
```

---

## What's Ready to Build Next
- The database schema is complete
- The API is 100% ready (no scraper data yet)
- The frontend UI is ready
- All infrastructure is Docker-ized

**Next action:** Implement The RealReal scraper in `backend/scrapers/realreal.py` and test with real data.

---

Last updated: March 9, 2026
