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
    ? 'text-pink-600'
    : velocity?.velocity_label === 'active'
      ? 'text-amber-600'
      : velocity?.velocity_label === 'stable'
        ? 'text-stone-700'
        : 'text-stone-500'

  return (
    <div className="min-h-screen bg-[#fffdf8]">
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

      <main className="mx-auto max-w-7xl px-4 py-6 sm:py-8">
        {searchParams?.watch === 'unsubscribed' && (
          <div className="mb-6 rounded-2xl border border-green-200 bg-green-50 px-4 py-3 text-sm text-green-700">
            Watch removed. You will not receive further alerts for this market.
          </div>
        )}

        <div className="flex flex-wrap items-center gap-2 text-sm text-stone-500">
          <Link href="/" className="transition-colors hover:text-stone-900">
            Feed
          </Link>
          <span>/</span>
          <span className="text-stone-700">{market.brand}</span>
          <span>/</span>
          <span className="text-stone-700">{displayModel}</span>
        </div>

        <section className="mt-6 rounded-3xl border border-stone-200 bg-[#f7f1e8] p-5 shadow-[0_12px_40px_rgba(206,182,150,0.10)] md:p-8">
          <div className="flex flex-col gap-8 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-3xl">
              <p className="mb-3 text-[11px] uppercase tracking-[0.3em] text-pink-500">Canonical Market Page</p>
              <h1 className="text-3xl font-semibold text-stone-900 sm:text-4xl md:text-5xl">
                {market.brand} {displayModel}
              </h1>
              <p className="mt-4 text-base leading-8 text-stone-600 md:text-lg">
                Live pricing across {market.platform_breakdown.length} platforms. This is the page BagDrop should rank
                for search traffic and share socially instead of pointing people straight to marketplace inventory.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 xl:min-w-[520px]">
              <div className="rounded-2xl border border-stone-200 bg-white/80 p-4">
                <p className="text-sm text-stone-500">Live listings</p>
                <p className="mt-2 text-3xl font-semibold text-stone-900">{market.stats.listing_count}</p>
              </div>
              <div className="rounded-2xl border border-stone-200 bg-white/80 p-4">
                <p className="text-sm text-stone-500">Lowest ask</p>
                <p className="mt-2 text-3xl font-semibold text-stone-900">{formatCurrency(market.stats.lowest_price)}</p>
              </div>
              <div className="rounded-2xl border border-stone-200 bg-white/80 p-4">
                <p className="text-sm text-stone-500">Avg drop</p>
                <p className="mt-2 text-3xl font-semibold text-pink-600">
                  {market.stats.average_drop_pct ? `-${formatPercent(market.stats.average_drop_pct)}` : 'N/A'}
                </p>
              </div>
              <div className="rounded-2xl border border-stone-200 bg-white/80 p-4">
                <p className="text-sm text-stone-500">Best drop</p>
                <p className="mt-2 text-3xl font-semibold text-pink-700">
                  {market.stats.biggest_drop_pct ? `-${formatPercent(market.stats.biggest_drop_pct)}` : 'N/A'}
                </p>
              </div>
            </div>
          </div>
        </section>

        <section className="mt-8 grid grid-cols-1 gap-8 xl:grid-cols-[0.75fr_1.25fr]">
          <div className="rounded-2xl border border-stone-200 bg-[#f7f1e8] p-5 shadow-[0_10px_30px_rgba(194,168,140,0.08)]">
            <p className="mb-2 text-[11px] uppercase tracking-[0.25em] text-pink-500">Platform Mix</p>
            <h2 className="text-xl font-semibold text-stone-900">Where inventory is showing up</h2>
            <div className="mt-5 space-y-3">
              {market.platform_breakdown.map((platform) => (
                <div
                  key={platform.platform}
                  className="flex items-center justify-between rounded-2xl border border-stone-200 bg-white/80 px-4 py-3"
                >
                  <span className="text-stone-700">{platformLabel(platform.platform)}</span>
                  <span className="rounded-full border border-stone-300 bg-[#fffaf2] px-3 py-1 text-xs font-mono text-stone-700">
                    {platform.listing_count} listings
                  </span>
                </div>
              ))}
            </div>

            <div className="mt-6 rounded-2xl border border-stone-200 bg-white/80 p-4 text-sm leading-7 text-stone-600 break-words">
              <p>
                Average ask: <span className="font-medium text-stone-900">{formatCurrency(market.stats.average_price)}</span>
              </p>
              <p>
                Canonical path: <span className="font-medium text-stone-900">{market.canonical_path}</span>
              </p>
            </div>

            {velocity && (
              <div className="mt-6 rounded-2xl border border-stone-200 bg-white/80 p-4">
                <p className="mb-2 text-[11px] uppercase tracking-[0.25em] text-pink-500">Velocity</p>
                <div className="flex items-end justify-between gap-4">
                  <div>
                    <p className={`text-3xl font-semibold ${velocityTone}`}>{velocity.velocity_score}</p>
                    <p className="mt-1 text-sm text-stone-500">
                      Supply is <span className={`font-medium ${velocityTone}`}>{velocity.velocity_label}</span>
                    </p>
                  </div>
                  <div className="text-right text-xs font-mono text-stone-500">
                    <p>{velocity.recent_listings_7d} new in 7d</p>
                    <p>{velocity.recent_listings_30d} new in 30d</p>
                  </div>
                </div>
                <p className="mt-4 text-sm leading-7 text-stone-600">
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
            <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="mb-2 text-[11px] uppercase tracking-[0.25em] text-pink-500">Inventory</p>
                <h2 className="text-2xl font-semibold text-stone-900">Current listings</h2>
              </div>
              <p className="text-sm text-stone-500">
                Sorted by largest markdown, then lowest ask.
              </p>
            </div>

            <div className="grid grid-cols-1 gap-5 md:grid-cols-2 2xl:grid-cols-3">
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
