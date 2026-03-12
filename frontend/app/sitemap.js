import { fetchApi } from '@/lib/api'
import { buildMarketPath } from '@/lib/slug'

const SITE_URL = 'https://bagdrop.xyz'
const LISTING_PAGE_SIZE = 500
const MAX_LISTING_PAGES = 20

async function fetchSitemapListings() {
  const listings = []

  for (let page = 0; page < MAX_LISTING_PAGES; page += 1) {
    const offset = page * LISTING_PAGE_SIZE
    const batch = await fetchApi(
      `/api/listings?sort_by=last_seen&limit=${LISTING_PAGE_SIZE}&offset=${offset}`
    )

    listings.push(...batch)

    if (batch.length < LISTING_PAGE_SIZE) {
      break
    }
  }

  return listings
}

export default async function sitemap() {
  let listings = []
  let featuredMarkets = []

  try {
    listings = await fetchSitemapListings()
  } catch {
    listings = []
  }

  try {
    featuredMarkets = await fetchApi('/api/markets/featured?limit=48&min_listings=1')
  } catch {
    featuredMarkets = []
  }

  const marketEntries = new Map()
  const listingEntries = listings.map((listing) => {
    const marketUrl = buildMarketPath(listing.brand, listing.model)
    const lastModified = listing.last_seen ? new Date(listing.last_seen) : new Date()
    const existingMarketEntry = marketEntries.get(marketUrl)

    if (!existingMarketEntry || existingMarketEntry.lastModified < lastModified) {
      marketEntries.set(marketUrl, {
        url: `${SITE_URL}${marketUrl}`,
        lastModified,
        changeFrequency: 'hourly',
        priority: 0.8,
      })
    }

    return {
      url: `${SITE_URL}/listings/${listing.id}`,
      lastModified,
      changeFrequency: 'hourly',
      priority: 0.7,
    }
  })

  for (const market of featuredMarkets) {
    if (!marketEntries.has(market.canonical_path)) {
      marketEntries.set(market.canonical_path, {
        url: `${SITE_URL}${market.canonical_path}`,
        lastModified: new Date(),
        changeFrequency: 'hourly',
        priority: 0.8,
      })
    }
  }

  return [
    {
      url: SITE_URL,
      lastModified: new Date(),
      changeFrequency: 'hourly',
      priority: 1,
    },
    {
      url: `${SITE_URL}/intel`,
      lastModified: new Date(),
      changeFrequency: 'daily',
      priority: 0.9,
    },
    ...marketEntries.values(),
    ...listingEntries,
  ]
}
