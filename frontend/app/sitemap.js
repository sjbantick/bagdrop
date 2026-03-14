import { fetchApi } from '@/lib/api'
import { buildMarketPath, slugifyValue } from '@/lib/slug'
import { SITE_URL } from '@/lib/site'

const LISTING_PAGE_SIZE = 500
const MAX_LISTING_PAGES = 20

async function fetchSitemapListings() {
  const listings = []
  let cursor = null

  for (let page = 0; page < MAX_LISTING_PAGES; page++) {
    const url = cursor
      ? `/api/listings?sort_by=last_seen&limit=${LISTING_PAGE_SIZE}&cursor=${cursor}`
      : `/api/listings?sort_by=last_seen&limit=${LISTING_PAGE_SIZE}`

    const data = await fetchApi(url)
    // API returns {items, next_cursor, has_more} or plain array (backwards compat)
    const items = data?.items ?? data ?? []
    listings.push(...items)

    if (!data?.has_more || !data?.next_cursor) break
    cursor = data.next_cursor
  }

  return listings
}

async function fetchWeeklyDropDates() {
  try {
    const weeks = await fetchApi('/api/intel/weekly-drops?weeks=12')
    return (weeks || []).filter((w) => w.listing_count > 0).map((w) => w.week_start)
  } catch {
    return []
  }
}

export default async function sitemap() {
  let listings = []
  let featuredMarkets = []
  let weeklyDropDates = []

  await Promise.all([
    fetchSitemapListings().then((r) => { listings = r }).catch(() => {}),
    fetchApi('/api/markets/featured?limit=48&min_listings=1').then((r) => { featuredMarkets = r }).catch(() => {}),
    fetchWeeklyDropDates().then((r) => { weeklyDropDates = r }).catch(() => {}),
  ])

  const marketEntries = new Map()
  const listingEntries = listings.map((listing) => {
    const marketUrl = buildMarketPath(listing.brand, listing.model)
    const lastModified = listing.last_seen ? new Date(listing.last_seen) : new Date()

    if (!marketEntries.has(marketUrl) || marketEntries.get(marketUrl).lastModified < lastModified) {
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

  const weeklyDropEntries = weeklyDropDates.map((date) => ({
    url: `${SITE_URL}/intel/weekly-drops/${date}`,
    lastModified: new Date(),
    changeFrequency: 'weekly',
    priority: 0.6,
  }))

  // Dedupe brand pages from the markets list
  const brandSet = new Set()
  for (const m of featuredMarkets) brandSet.add(m.brand)
  const brandEntries = [...brandSet].map((brand) => ({
    url: `${SITE_URL}/${slugifyValue(brand)}`,
    lastModified: new Date(),
    changeFrequency: 'daily',
    priority: 0.8,
  }))

  return [
    { url: SITE_URL, lastModified: new Date(), changeFrequency: 'hourly', priority: 1 },
    { url: `${SITE_URL}/markets`, lastModified: new Date(), changeFrequency: 'daily', priority: 0.9 },
    { url: `${SITE_URL}/intel`, lastModified: new Date(), changeFrequency: 'daily', priority: 0.9 },
    { url: `${SITE_URL}/intel/weekly-drops`, lastModified: new Date(), changeFrequency: 'weekly', priority: 0.7 },
    ...weeklyDropEntries,
    ...brandEntries,
    ...marketEntries.values(),
    ...listingEntries,
  ]
}
