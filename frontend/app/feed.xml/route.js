import { fetchApi } from '@/lib/api'
import { SITE_URL } from '@/lib/site'

function esc(str) {
  if (!str) return ''
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&apos;')
}

function platformLabel(platform) {
  const labels = {
    fashionphile: 'Fashionphile',
    rebag: 'Rebag',
    realreal: 'The RealReal',
    vestiaire: 'Vestiaire',
    yoogi: "Yoogi's Closet",
    cosette: 'Cosette',
    thepurseaffair: 'The Purse Affair',
    luxedh: 'LuxeDH',
    madisonavenuecouture: 'Madison Avenue Couture',
  }
  return labels[platform] || platform
}

function titleCase(value) {
  return (value || '')
    .split(/\s+/)
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

export async function GET() {
  let listings = []
  try {
    const data = await fetchApi('/api/listings?limit=50&sort_by=drop_pct&min_drop_pct=1')
    listings = data?.items ?? data ?? []
  } catch {
    listings = []
  }

  const now = new Date().toUTCString()

  const items = listings
    .map((listing) => {
      const displayModel = titleCase(listing.model)
      const platform = platformLabel(listing.platform)
      const dropLine = listing.drop_pct
        ? ` — down ${Number(listing.drop_pct).toFixed(1)}% ($${Math.round(listing.drop_amount || 0)} off)`
        : ''
      const priceWas =
        listing.original_price && listing.original_price !== listing.current_price
          ? ` Previously $${Math.round(listing.original_price).toLocaleString()}.`
          : ''
      const condition = listing.condition ? ` Condition: ${titleCase(listing.condition)}.` : ''
      const size = listing.size ? ` Size: ${listing.size}.` : ''
      const color = listing.color ? ` Color: ${titleCase(listing.color)}.` : ''
      const description = `${platform} listing at $${Math.round(listing.current_price).toLocaleString()}${dropLine}.${priceWas}${condition}${size}${color}`
      const url = `${SITE_URL}/listings/${listing.id}`
      const pubDate = new Date(listing.first_seen || listing.last_seen).toUTCString()

      return `
    <item>
      <title>${esc(`${listing.brand} ${displayModel} — $${Math.round(listing.current_price).toLocaleString()} on ${platform}${listing.drop_pct ? ` (−${Number(listing.drop_pct).toFixed(1)}%)` : ''}`)}</title>
      <link>${esc(url)}</link>
      <guid isPermaLink="true">${esc(url)}</guid>
      <description>${esc(description)}</description>
      <pubDate>${pubDate}</pubDate>
      ${listing.photo_url ? `<enclosure url="${esc(listing.photo_url)}" type="image/jpeg" length="0"/>` : ''}
    </item>`
    })
    .join('')

  const xml = `<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>BagDrop — Luxury Handbag Price Drops</title>
    <link>${SITE_URL}</link>
    <atom:link href="${SITE_URL}/feed.xml" rel="self" type="application/rss+xml"/>
    <description>Real-time luxury handbag price drop tracker across Fashionphile, Rebag, The RealReal, Vestiaire, and more.</description>
    <language>en-us</language>
    <lastBuildDate>${now}</lastBuildDate>
    <ttl>30</ttl>
    <image>
      <url>${SITE_URL}/opengraph-image</url>
      <title>BagDrop</title>
      <link>${SITE_URL}</link>
    </image>
${items}
  </channel>
</rss>`

  return new Response(xml, {
    headers: {
      'Content-Type': 'application/rss+xml; charset=utf-8',
      'Cache-Control': 'public, max-age=1800, stale-while-revalidate=3600',
    },
  })
}
