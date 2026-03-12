# BagDrop Launch Checklist

## Objective

Ship BagDrop as a live, indexable traffic engine with:

- working scrapers
- tracked outbound marketplace clicks
- visible operational health
- enough SEO surface to begin ranking

## 1. Backend Deployment

- Create or reuse the Railway backend service from the repo root.
- Confirm Railway uses [railway.toml](/Users/sambantick/Downloads/bagdrop/railway.toml).
- Confirm the backend image builds from `backend/Dockerfile`.
- Confirm the service starts with:
  ```bash
  uvicorn main:app --host 0.0.0.0 --port $PORT
  ```

Required backend environment variables:

```text
DATABASE_URL=<Railway Postgres connection string>
REDIS_URL=<Railway Redis connection string>
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=false
PUBLIC_APP_URL=https://thebagdrop.xyz
PUBLIC_API_URL=https://bagdrop-api-production.up.railway.app
OUTBOUND_UTM_SOURCE=bagdrop
REALREAL_AFFILIATE_QUERY=
VESTIAIRE_AFFILIATE_QUERY=
FASHIONPHILE_AFFILIATE_QUERY=
REBAG_AFFILIATE_QUERY=
WATCH_TOKEN_SECRET=<random long secret>
ALERT_FROM_EMAIL=alerts@thebagdrop.xyz
ALERT_REPLY_TO=hello@thebagdrop.xyz
OPS_DASHBOARD_TOKEN=<random long secret>
SMTP_HOST=<smtp host>
SMTP_PORT=587
SMTP_USERNAME=<smtp username>
SMTP_PASSWORD=<smtp password>
SMTP_USE_TLS=true
SMTP_USE_SSL=false
ENABLE_REALREAL=true
ENABLE_VESTIAIRE=true
ENABLE_FASHIONPHILE=true
ENABLE_REBAG=true
```

Backend launch checks:

- `GET /health` returns `200`
- `GET /api/stats` returns live JSON
- `GET /api/admin/ops-summary` returns all monitored platforms
- `POST /api/admin/watchlists/send?dry_run=true` returns a valid summary
- initial scrape runs after startup without crashing the service

## 2. Frontend Deployment

- Deploy the `frontend/` app as a separate service.
- Confirm Railway uses [frontend/railway.toml](/Users/sambantick/Downloads/bagdrop/frontend/railway.toml).
- Confirm the frontend image builds from `frontend/Dockerfile`.
- Set:

```text
NEXT_PUBLIC_API_URL=https://bagdrop-api-production.up.railway.app
NEXT_PUBLIC_SITE_URL=https://thebagdrop.xyz
OPS_DASHBOARD_TOKEN=<same backend ops token>
```

Frontend launch checks:

- homepage loads with live stats and listings
- `/[brand]/[model]` market pages render from production data
- `/listings/[listingId]` pages render from production data
- `/sitemap.xml` loads successfully
- `/robots.txt` points to the production sitemap
- watchlist unsubscribe redirect lands back on the relevant market page

## 3. Domain Cutover

- Point `thebagdrop.xyz` to the frontend deployment.
- Keep the Railway backend on `bagdrop-api-production.up.railway.app` unless a custom API domain is added on a higher plan.
- Force HTTPS on both hosts.
- Re-test:
  - `https://thebagdrop.xyz`
  - `https://thebagdrop.xyz/sitemap.xml`
  - `https://bagdrop-api-production.up.railway.app/health`
  - `https://bagdrop-api-production.up.railway.app/api/admin/ops-summary`

## 4. GitHub Actions Configuration

The repo now contains:

- `.github/workflows/ci.yml`
- `.github/workflows/ops-check.yml`

Configure these in GitHub after production URLs are stable:

```text
Secret: BAGDROP_OPS_URL=https://bagdrop-api-production.up.railway.app/api/admin/ops-summary
Secret: BAGDROP_OPS_TOKEN=<same backend ops token>
Variable (optional): BAGDROP_REQUIRE_CLICKS=true
```

Expected behavior:

- `CI` runs on pushes to `main` and pull requests
- `Ops Check` runs every 6 hours and on manual dispatch
- Vercel's native GitHub integration deploys the frontend on pushes to `main`

## 5. Monetization Activation

Before public launch, add any available platform-specific affiliate params:

```text
REALREAL_AFFILIATE_QUERY=?ref={{listing_id}}&surface={{surface}}
VESTIAIRE_AFFILIATE_QUERY=?ref={{listing_id}}&market={{market_slug}}
FASHIONPHILE_AFFILIATE_QUERY=?ref={{listing_id}}&placement={{surface}}
REBAG_AFFILIATE_QUERY=?ref={{listing_id}}&market={{market_slug}}
```

Verification:

- click a marketplace CTA from a listing card
- click a marketplace CTA from a listing detail page
- confirm BagDrop logs the click first, then redirects with UTM params
- confirm affiliate params survive on the outbound URL
- confirm watchlist emails contain unsubscribe links that resolve against `bagdrop-api-production.up.railway.app`

## 6. Smoke Test Path

Run these checks immediately after deployment:

```bash
python3 scripts/check_ops.py --url https://bagdrop-api-production.up.railway.app/api/admin/ops-summary --token "$BAGDROP_OPS_TOKEN"
```

Then manually verify:

- homepage shows live inventory
- at least one market page loads
- at least one listing detail page loads
- outbound click redirect works
- `/ops` shows fresh platforms after scrapes complete
- `python3 scripts/send_watch_alerts.py --dry-run` returns a non-error summary in the deployed environment

## 7. Launch Decision

Launch only if all of the following are true:

- backend is healthy
- frontend is healthy
- domain routing is correct
- scrapers are producing active listings
- outbound click tracking works
- monitoring is configured
- at least one monetization path is active or ready to activate

## Current Blocking Items

- production deployment completion
- domain routing
- live affiliate params
- SMTP credentials for watch alerts and intelligence digests
