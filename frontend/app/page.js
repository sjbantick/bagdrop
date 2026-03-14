import HomePageClient from '@/components/HomePageClient'
import { fetchApi } from '@/lib/api'

async function safeFetch(path, fallback) {
  try {
    return await fetchApi(path)
  } catch {
    return fallback
  }
}

export default async function HomePage() {
  const [
    initialListingsPage,
    initialStats,
    initialFeaturedMarkets,
    initialArbitrageOpportunities,
    initialBagIndex,
    initialNewDrops,
  ] = await Promise.all([
    safeFetch('/api/listings?limit=60&sort_by=drop_pct&min_drop_pct=0', []),
    safeFetch('/api/stats', null),
    safeFetch('/api/markets/featured?limit=6&min_listings=2', []),
    safeFetch('/api/opportunities/arbitrage?limit=6&min_gap_pct=15', []),
    safeFetch('/api/bag-index?limit=6&live=true&min_active_listings=2', []),
    safeFetch('/api/opportunities/new-drops?limit=6&hours=72&min_significance=40', []),
  ])

  const initialListings = initialListingsPage?.items ?? initialListingsPage ?? []

  return (
    <HomePageClient
      initialListings={initialListings}
      initialStats={initialStats}
      initialFeaturedMarkets={initialFeaturedMarkets}
      initialArbitrageOpportunities={initialArbitrageOpportunities}
      initialBagIndex={initialBagIndex}
      initialNewDrops={initialNewDrops}
    />
  )
}
