# BagDrop TODOS

Generated from CEO plan review — 2026-03-14.

## Phase 2 (next sprint)

### P1: Affiliate Revenue
- **Wire affiliate params**: Sign up for/confirm affiliate accounts on Fashionphile, Rebag, The RealReal, Vestiaire. Set `FASHIONPHILE_AFFILIATE_QUERY`, `REBAG_AFFILIATE_QUERY`, `REALREAL_AFFILIATE_QUERY`, `VESTIAIRE_AFFILIATE_QUERY` env vars in Railway. Every outbound click currently earns $0.

### P1: Performance
- **Cursor-based pagination on /api/listings**: Add `?cursor=` and `?limit=50` params. Frontend infinite scroll on feed. Required before 50k listings. See: `routers/listings.py` `get_listings()`.
- **Redis caching for hot paths**: Cache `/api/stats`, `/api/brands`, `/api/bag-index` in Redis with 15-min TTL. Redis is already in the stack (`config.redis_url`) but unused.

### P2: Product differentiation
- **Deal Score per listing**: Composite 0–100 metric combining `drop_pct`, days on market, condition grade, and platform competition (how many similar listings exist). Add to `ListingResponse`, display on `ListingCard`.
- **Price drop velocity badge**: Show directional momentum on listing cards: "↓ dropped 3% in 24h" vs. "→ holding 5 days". Compute from `PriceHistory`. Add to `ListingResponse`.
- **Cross-platform comparison on listing detail**: "Other [brand] [model] available now: [3 listings from other platforms]". Query by brand+model, surface top 3 competitors. Turns listing pages from dead-ends into shopping tools.
- **Save search / feed watchlist**: Bookmark icon on feed filters. User sets Brand=Chanel, max price=$2000, saves → becomes a watchlist subscription. Needs `WatchSubscription` schema extension (brand-only, price-range).
- **Per-listing price alert**: "Alert me if this Birkin drops below $7,500." New `ListingPriceAlert` model + scheduler check. Highest-intent conversion point.

## Phase 3

### Monetization
- **Stripe premium tier**: $9/mo subscription. Unlocks: Deal Score, unlimited saved searches, priority alerts, no cooldowns. Build after affiliate revenue is proven.
- **Auto-generated editorial SEO pages**: Weekly "Best Drops" at `/intel/weekly-drops/YYYY-MM-DD` built from real data (top 10 listings by Deal Score with context). SEO compound interest play — start the archive early.

## Operational
- **Update BUILD_STATUS.md**: Still says "4 scrapers". Update to reflect current 9 (fashionphile, rebag, realreal, vestiaire, yoogi, cosette, thepurseaffair, luxedh, madisonavenuecouture).
- **Verify SMTP delivery end-to-end**: SMTP is configured (Resend) but never verified in production. Run `POST /api/admin/watchlists/send?dry_run=false` with a test subscription.
- **Verify ALERT_FROM_EMAIL is set in Railway**: `alerts@thebagdrop.xyz` must be a verified Resend sender domain.

## Architecture (deferred)
- **Alembic migrations**: Add when next schema change is needed. Currently using `create_all()` which is fine while schema is stable.
- **B2B data API**: Phase 5+. Licensing price intelligence to other tools. Off critical path until affiliate and subscription revenue is proven.
