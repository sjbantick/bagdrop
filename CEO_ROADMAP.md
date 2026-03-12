# BagDrop CEO Roadmap

## Mandate

Paperclip is no longer the execution layer for BagDrop. This repository is now the operating system for the company.

From this point forward:
- strategy lives here
- priorities live here
- execution is driven directly from code and repo docs
- low-value scope is cut aggressively

## Product Thesis

BagDrop wins if it becomes the fastest way to see meaningful luxury handbag markdowns across major resale platforms, then turns that traffic into monetizable outbound intent.

The product does **not** need to be a full luxury resale platform.
It needs to be:
- fast
- indexable
- credible
- useful on first visit
- instrumented for monetization

## Current Position

### Already Built
- FastAPI backend
- 4 scrapers
- scheduler
- listing feed
- listing detail pages
- canonical market pages
- sitemap and robots support

### Not Done
- production deployment completion
- affiliate attribution and outbound click tracking
- monitoring / scrape-failure alerting
- email/watchlist retention loop
- real market intelligence features beyond the current schema

## New Direction

The company is now focused on a **Launchable Traffic Engine**, not a maximal feature set.

That means:

### Priority 1: Launch
Ship a stable public product with working backend, frontend, domain, and scheduled scrapes.

### Priority 2: Monetize Existing Traffic
Add affiliate instrumentation and clean outbound flows before building premium complexity.

### Priority 3: Retain
Add watchlists / alerts only after launch and monetized click flow are working.

### Priority 4: Deepen Moat
Add arbitrage, velocity scoring, and stronger BagIndex logic after the site is live and indexed.

## Explicit Cuts

These are not current priorities:
- B2B API
- broad enterprise positioning
- large outreach CRM workflows
- Stripe premium subscription before core outbound monetization works
- complex admin systems unless directly needed for launch reliability

They may come back later, but they are off the critical path now.

## Execution Rules

1. Prefer shipping over planning.
2. Prefer one clear path over parallel experiments.
3. Prefer owned pages over sending users straight off-site.
4. Prefer monetization instrumentation over speculative intelligence features.
5. Prefer reliability and deployment over adding more feature surface.

## Source of Truth

### Active Docs
- `BUILD_STATUS.md` = actual build state
- `README.md` = public/dev overview
- `CEO_ROADMAP.md` = company direction and execution priorities

## Current CEO Queue

### Now
1. Finish frontend/domain cutover and remove the current Vercel SSO bottleneck
2. Configure the GitHub Actions ops check against the production backend URL
3. Set production SMTP and scheduler config so watch alerts and the intelligence digest run live

### Next
1. Seed live platform affiliate query templates on top of the tracked redirect flow and use `/ops` click analytics to validate them
2. Expand editorial SEO beyond inventory-backed pages
3. Turn `/intel`, digests, and the intelligence stack into stronger retention and sharing loops

### Later
1. Premium subscriptions
2. B2B access
3. broader content/growth systems

## Definition of Launch Ready

BagDrop is launch ready when all of the following are true:
- production backend is live
- production frontend is live
- domain is connected
- scheduled scrapes run successfully
- key pages render with real data
- outbound links are tracked
- at least one monetization path is active
- failures are visible quickly

## Decision

The company is no longer optimizing for "complete feature map."
It is optimizing for:

**launch fast, rank pages, capture click intent, then deepen the moat**

Last updated: March 12, 2026
