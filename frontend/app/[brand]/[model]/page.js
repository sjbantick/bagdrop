import Link from 'next/link'
import { notFound } from 'next/navigation'
import Header from '@/components/Header'
import ListingCard from '@/components/ListingCard'
import WatchMarketCard from '@/components/WatchMarketCard'
import StructuredData from '@/components/StructuredData'
import { fetchApi } from '@/lib/api'
import { formatCurrency, formatPercent, platformLabel, titleCase } from '@/lib/format'
import { absoluteUrl } from '@/lib/site'

async function getMarket(brand, model) {
  try {
    return await fetchApi(`/api/markets/${brand}/${model}?limit=36`)
  } catch {
    return null
  }
}

async function getVelocity(brand, model) {
  try {
    return await fetchApi(`/api/markets/${brand}/${model}/velocity`)
  } catch {
    return null
  }
}

export async function generateMetadata({ params }) {
  const market = await getMarket(params.brand, params.model)

  if (!market) {
    return {
      title: 'Market Not Found | BagDrop',
    }
  }

  const displayModel = titleCase(market.model)
  const avgDrop = market.stats.average_drop_pct ? `-${formatPercent(market.stats.average_drop_pct)}` : 'tracked'

  return {
    title: `${market.brand} ${displayModel} resale prices | BagDrop`,
    description: `${market.stats.listing_count} live ${market.brand} ${displayModel} listings with ${avgDrop} average markdown across luxury resale platforms.`,
    alternates: {
      canonical: market.canonical_path,
    },
    openGraph: {
      title: `${market.brand} ${displayModel} resale prices | BagDrop`,
      description: `${market.stats.listing_count} live ${market.brand} ${displayModel} listings with ${avgDrop} average markdown across luxury resale platforms.`,
      url: market.canonical_path,
      type: 'article',
      images: [
        {
          url: absoluteUrl(`${market.canonical_path}/opengraph-image`),
          width: 1200,
          height: 630,
          alt: `${market.brand} ${displayModel} market overview`,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title: `${market.brand} ${displayModel} resale prices | BagDrop`,
      description: `${market.stats.listing_count} live ${market.brand} ${displayModel} listings with ${avgDrop} average markdown across luxury resale platforms.`,
      images: [absoluteUrl(`${market.canonical_path}/opengraph-image`)],
    },
  }
}

export default async function MarketPage({ params, searchParams }) {
  const market = await getMarket(params.brand, params.model)
  if (!market) {
    notFound()
  }

  const velocity = await getVelocity(params.brand, params.model)

  const displayModel = titleCase(market.model)
  const velocityTone = velocity?.velocity_label === 'hot'
    ? 'text-red-400'
    : velocity?.velocity_label === 'active'
      ? 'text-orange-300'
      : velocity?.velocity_label === 'stable'
        ? 'text-yellow-200'
        : 'text-gray-300'

  return (
    <div className="min-h-screen bg-black">
      <StructuredData
        data={{
          '@context': 'https://schema.org',
          '@type': 'CollectionPage',
          name: `${market.brand} ${displayModel} resale market`,
          description: `${market.stats.listing_count} live ${market.brand} ${displayModel} listings across BagDrop-tracked resale platforms.`,
          url: absoluteUrl(market.canonical_path),
          mainEntity: {
            '@type': 'ItemList',
            itemListElement: market.listings.slice(0, 12).map((listing, index) => ({
              '@type': 'ListItem',
              position: index + 1,
              url: absoluteUrl(`/listings/${listing.id}`),
              name: `${listing.brand} ${titleCase(listing.model)}`,
            })),
          },
        }}
      />
      <Header />

      <main className="max-w-7xl mx-auto px-4 py-8">
        {searchParams?.watch === 'unsubscribed' && (
          <div className="mb-6 rounded-2xl border border-green-500/30 bg-green-500/10 px-4 py-3 text-sm text-green-300">
            Watch removed. You will not receive further alerts for this market.
          </div>
        )}

        <div className="flex flex-wrap items-center gap-2 text-sm text-gray-500">
          <Link href="/" className="hover:text-white transition-colors">
            Feed
          </Link>
          <span>/</span>
          <span className="text-gray-300">{market.brand}</span>
          <span>/</span>
          <span className="text-gray-300">{displayModel}</span>
        </div>

        <section className="mt-6 rounded-3xl border border-gray-800 bg-gradient-to-br from-gray-950 via-black to-gray-950 p-6 md:p-8">
          <div className="flex flex-col gap-8 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-3xl">
              <p className="text-[11px] uppercase tracking-[0.3em] text-red-500 mb-3">Canonical Market Page</p>
              <h1 className="text-4xl md:text-5xl font-semibold text-white">
                {market.brand} {displayModel}
              </h1>
              <p className="mt-4 text-base md:text-lg leading-8 text-gray-300">
                Live pricing across {market.platform_breakdown.length} platforms. This is the page BagDrop should rank
                for search traffic and share socially instead of pointing people straight to marketplace inventory.
              </p>
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 xl:min-w-[520px]">
              <div className="rounded-2xl border border-gray-800 bg-black/60 p-4">
                <p className="text-gray-500 text-sm">Live listings</p>
                <p className="mt-2 text-3xl font-semibold text-white">{market.stats.listing_count}</p>
              </div>
              <div className="rounded-2xl border border-gray-800 bg-black/60 p-4">
                <p className="text-gray-500 text-sm">Lowest ask</p>
                <p className="mt-2 text-3xl font-semibold text-white">{formatCurrency(market.stats.lowest_price)}</p>
              </div>
              <div className="rounded-2xl border border-gray-800 bg-black/60 p-4">
                <p className="text-gray-500 text-sm">Avg drop</p>
                <p className="mt-2 text-3xl font-semibold text-red-400">
                  {market.stats.average_drop_pct ? `-${formatPercent(market.stats.average_drop_pct)}` : 'N/A'}
                </p>
              </div>
              <div className="rounded-2xl border border-gray-800 bg-black/60 p-4">
                <p className="text-gray-500 text-sm">Best drop</p>
                <p className="mt-2 text-3xl font-semibold text-red-500">
                  {market.stats.biggest_drop_pct ? `-${formatPercent(market.stats.biggest_drop_pct)}` : 'N/A'}
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="mt-8 grid grid-cols-1 xl:grid-cols-[0.75fr_1.25fr] gap-8">
          <div className="rounded-2xl border border-gray-800 bg-gray-950 p-5">
            <p className="text-[11px] uppercase tracking-[0.25em] text-red-500 mb-2">Platform Mix</p>
            <h2 className="text-xl font-semibold text-white">Where inventory is showing up</h2>
            <div className="mt-5 space-y-3">
              {market.platform_breakdown.map((platform) => (
                <div
                  key={platform.platform}
                  className="flex items-center justify-between rounded-2xl border border-gray-800 bg-black/50 px-4 py-3"
                >
                  <span className="text-gray-300">{platformLabel(platform.platform)}</span>
                  <span className="rounded-full border border-gray-700 px-3 py-1 text-xs font-mono text-white">
                    {platform.listing_count} listings
                  </span>
                </div>
              ))}
            </div>

            <div className="mt-6 rounded-2xl border border-gray-800 bg-black/50 p-4 text-sm leading-7 text-gray-300">
              <p>
                Average ask: <span className="text-white">{formatCurrency(market.stats.average_price)}</span>
              </p>
              <p>
                Canonical path: <span className="text-white">{market.canonical_path}</span>
              </p>
            </div>

            {velocity && (
              <div className="mt-6 rounded-2xl border border-gray-800 bg-black/50 p-4">
                <p className="text-[11px] uppercase tracking-[0.25em] text-red-500 mb-2">Velocity</p>
                <div className="flex items-end justify-between gap-4">
                  <div>
                    <p className={`text-3xl font-semibold ${velocityTone}`}>{velocity.velocity_score}</p>
                    <p className="mt-1 text-sm text-gray-400">
                      Supply is <span className={`font-medium ${velocityTone}`}>{velocity.velocity_label}</span>
                    </p>
                  </div>
                  <div className="text-right text-xs font-mono text-gray-500">
                    <p>{velocity.recent_listings_7d} new in 7d</p>
                    <p>{velocity.recent_listings_30d} new in 30d</p>
                  </div>
                </div>
                <p className="mt-4 text-sm leading-7 text-gray-300">
                  Velocity is inferred from recent first-seen activity across active listings. High scores mean fresh
                  supply is hitting this market quickly.
                </p>
              </div>
            )}

            <div className="mt-6">
              <WatchMarketCard
                brand={market.brand}
                model={displayModel}
                listingCount={market.stats.listing_count}
              />
            </div>
          </div>

          <div>
            <div className="flex items-end justify-between gap-4 mb-4">
              <div>
                <p className="text-[11px] uppercase tracking-[0.25em] text-red-500 mb-2">Inventory</p>
                <h2 className="text-2xl font-semibold text-white">Current listings</h2>
              </div>
              <p className="text-sm text-gray-500">
                Sorted by largest markdown, then lowest ask.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 2xl:grid-cols-3 gap-5">
              {market.listings.map((listing) => (
                <ListingCard key={listing.id} listing={listing} />
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  )
}
