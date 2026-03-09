# BagDrop — bagdrop.xyz

Real-time luxury handbag price drop tracker. Scans The RealReal, Vestiaire Collective, Fashionphile and Rebag daily to surface motivated sellers and buying opportunities.

## Stack
- **Scraping**: Python + Playwright/httpx
- **Backend**: FastAPI + PostgreSQL + Redis
- **Frontend**: Next.js + Tailwind (dark, urgency aesthetic like panicselling.xyz)
- **Infra**: Railway or Render for fast deployment

## Data Model
Each listing has: platform, url, brand, model, size, color, hardware, condition, current_price, original_price, drop_amount, drop_pct, first_seen, last_updated

## Key Rules
- Always normalize brand/model names consistently across platforms
- Store price history — never overwrite, always append
- Scrape respectfully: rate limit, randomize user agents, respect robots.txt
- Never store PII

## Projects
- Data Infrastructure — scrapers, DB schema, price history pipeline
- Web App — Next.js frontend feed, filters, price charts
- Price Intelligence — cross-platform arbitrage, velocity scoring, bag index
- Growth & Distribution — SEO, content, social, email
- Monetization — affiliate links, premium alerts, B2B API
