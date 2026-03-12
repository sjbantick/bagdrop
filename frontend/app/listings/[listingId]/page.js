import Link from 'next/link'
import { notFound } from 'next/navigation'
import Header from '@/components/Header'
import ListingCard from '@/components/ListingCard'
import PriceHistoryChart from '@/components/PriceHistoryChart'
import ReportListingCard from '@/components/ReportListingCard'
import StructuredData from '@/components/StructuredData'
import { buildOutboundUrl, fetchApi } from '@/lib/api'
import { buildMarketPath } from '@/lib/slug'
import { formatCurrency, formatPercent, freshnessLabel, platformLabel, titleCase } from '@/lib/format'
import { absoluteUrl } from '@/lib/site'

async function getListing(listingId) {
  try {
    return await fetchApi(`/api/listings/${listingId}`)
  } catch {
    return null
  }
}

async function getHistory(listingId) {
  try {
    return await fetchApi(`/api/listings/${listingId}/price-history`)
  } catch {
    return []
  }
}

async function getRelatedListings(listing) {
  try {
    const market = await fetchApi(
      `/api/markets/${buildMarketPath(listing.brand, listing.model).slice(1)}?limit=4`
    )
    return market.listings.filter((item) => item.id !== listing.id).slice(0, 3)
  } catch {
    return []
  }
}

export async function generateMetadata({ params }) {
  const listing = await getListing(params.listingId)

  if (!listing) {
    return {
      title: 'Listing Not Found | BagDrop',
    }
  }

  const dropText = listing.drop_pct ? `-${formatPercent(listing.drop_pct)}` : 'price-tracked'
  const marketPath = buildMarketPath(listing.brand, listing.model)
  const pagePath = `/listings/${listing.id}`
  const description = `${platformLabel(listing.platform)} listing at ${formatCurrency(listing.current_price)} with BagDrop price history and market context.`

  return {
    title: `${listing.brand} ${titleCase(listing.model)} ${dropText} | BagDrop`,
    description,
    alternates: {
      canonical: pagePath,
    },
    openGraph: {
      title: `${listing.brand} ${titleCase(listing.model)} ${dropText} | BagDrop`,
      description,
      url: pagePath,
      type: 'article',
      images: [
        {
          url: absoluteUrl(`${pagePath}/opengraph-image`),
          width: 1200,
          height: 630,
          alt: `${listing.brand} ${titleCase(listing.model)} listing summary`,
        },
      ],
    },
    twitter: {
      card: 'summary_large_image',
      title: `${listing.brand} ${titleCase(listing.model)} ${dropText} | BagDrop`,
      description,
      images: [absoluteUrl(`${pagePath}/opengraph-image`)],
    },
    other: {
      'bagdrop:market': absoluteUrl(marketPath),
    },
  }
}

export default async function ListingDetailPage({ params }) {
  const listing = await getListing(params.listingId)
  if (!listing) {
    notFound()
  }

  const [history, relatedListings] = await Promise.all([
    getHistory(listing.id),
    getRelatedListings(listing),
  ])

  const marketPath = buildMarketPath(listing.brand, listing.model)
  const platformName = platformLabel(listing.platform)
  const displayModel = titleCase(listing.model)
  const outboundUrl = buildOutboundUrl(listing.id, 'listing_detail', 'listing_page')

  return (
    <div className="min-h-screen bg-[#fffdf8]">
      <StructuredData
        data={{
          '@context': 'https://schema.org',
          '@type': 'Product',
          name: `${listing.brand} ${displayModel}`,
          image: listing.photo_url ? [listing.photo_url] : undefined,
          description: listing.description || `${platformName} listing tracked by BagDrop.`,
          brand: {
            '@type': 'Brand',
            name: listing.brand,
          },
          offers: {
            '@type': 'Offer',
            priceCurrency: 'USD',
            price: listing.current_price,
            availability: 'https://schema.org/InStock',
            url: absoluteUrl(`/listings/${listing.id}`),
            seller: {
              '@type': 'Organization',
              name: platformName,
            },
          },
        }}
      />
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-6 sm:py-8">
        <div className="flex flex-wrap items-center gap-2 text-sm text-stone-500">
          <Link href="/" className="transition-colors hover:text-stone-900">
            Feed
          </Link>
          <span>/</span>
          <Link href={marketPath} className="transition-colors hover:text-stone-900">
            {listing.brand} {displayModel}
          </Link>
          <span>/</span>
          <span className="text-stone-700">{platformName}</span>
        </div>

        <div className="mt-6 grid grid-cols-1 items-start gap-8 lg:grid-cols-[1.1fr_0.9fr]">
          <section className="overflow-hidden rounded-3xl border border-stone-200 bg-[#f6efe4]">
            <div className="aspect-[4/3] bg-gradient-to-br from-[#efe4d6] via-[#f8f1e7] to-[#ede0d0]">
              {listing.photo_url ? (
                <img
                  src={listing.photo_url}
                  alt={`${listing.brand} ${displayModel}`}
                  className="w-full h-full object-cover"
                />
              ) : (
                <div className="flex h-full w-full items-center justify-center text-stone-500">
                  {listing.brand} {displayModel}
                </div>
              )}
            </div>
          </section>

          <section className="rounded-3xl border border-stone-200 bg-white p-5 shadow-[0_12px_40px_rgba(206,182,150,0.12)] sm:p-6">
            <div className="mb-4 flex flex-wrap gap-2 text-xs font-mono">
              <span className="rounded-full border border-pink-300 bg-pink-50 px-3 py-1 text-pink-600">
                {listing.drop_pct ? `-${formatPercent(listing.drop_pct)}` : 'Tracked'}
              </span>
              <span className="rounded-full border border-stone-300 bg-[#fffaf2] px-3 py-1 text-stone-700">
                {platformName}
              </span>
              <span className="rounded-full border border-stone-300 bg-[#fffaf2] px-3 py-1 text-stone-700">
                {listing.condition}
              </span>
            </div>

            <p className="text-sm uppercase tracking-[0.2em] text-stone-500">{listing.brand}</p>
            <h1 className="mt-2 text-3xl font-semibold text-stone-900 sm:text-4xl">{displayModel}</h1>

            <div className="mt-6 flex flex-col gap-3 sm:flex-row sm:items-end">
              <div>
                <p className="text-sm text-stone-500">Current ask</p>
                <p className="text-3xl font-semibold text-stone-900 sm:text-4xl">{formatCurrency(listing.current_price)}</p>
              </div>
              {listing.original_price && listing.original_price !== listing.current_price && (
                <div className="pb-1">
                  <p className="text-sm text-stone-500">Was</p>
                  <p className="text-xl text-stone-400 line-through">{formatCurrency(listing.original_price)}</p>
                </div>
              )}
            </div>

            <div className="mt-8 grid grid-cols-1 gap-4 text-sm sm:grid-cols-2">
              <div className="rounded-2xl border border-stone-200 bg-[#fffaf2] p-4">
                <p className="text-stone-500">Markdown</p>
                <p className="mt-2 text-xl font-semibold text-pink-600">
                  {listing.drop_amount ? `-${formatCurrency(listing.drop_amount)}` : 'N/A'}
                </p>
              </div>
              <div className="rounded-2xl border border-stone-200 bg-[#fffaf2] p-4">
                <p className="text-stone-500">Freshness</p>
                <p className="mt-2 text-xl font-semibold text-stone-900">
                  {freshnessLabel(listing.last_seen)}
                </p>
              </div>
              <div className="rounded-2xl border border-stone-200 bg-[#fffaf2] p-4">
                <p className="text-stone-500">Size</p>
                <p className="mt-2 text-xl font-semibold text-stone-900">{listing.size || 'Not listed'}</p>
              </div>
              <div className="rounded-2xl border border-stone-200 bg-[#fffaf2] p-4">
                <p className="text-stone-500">Color</p>
                <p className="mt-2 text-xl font-semibold text-stone-900">{listing.color || 'Not listed'}</p>
              </div>
            </div>

            {listing.description && (
              <div className="mt-8 border-t border-stone-200 pt-6">
                <p className="mb-3 text-[11px] uppercase tracking-[0.25em] text-pink-500">Listing Notes</p>
                <p className="text-sm leading-7 text-stone-600">{listing.description}</p>
              </div>
            )}

            <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:flex-wrap">
              <a
                href={outboundUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center justify-center rounded-full bg-pink-500 px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-pink-400"
              >
                View on {platformName}
              </a>
              <Link
                href={marketPath}
                className="inline-flex items-center justify-center rounded-full border border-stone-300 px-5 py-3 text-sm font-medium text-stone-700 transition-colors hover:border-pink-300 hover:text-pink-600"
              >
                See this market
              </Link>
            </div>
          </section>
        </div>

        <div className="mt-8 grid grid-cols-1 gap-8 xl:grid-cols-[0.9fr_1.1fr]">
          <PriceHistoryChart history={history} />

          <section className="rounded-2xl border border-stone-200 bg-[#fffaf2] p-5">
            <p className="mb-2 text-[11px] uppercase tracking-[0.25em] text-pink-500">Why It Matters</p>
            <h2 className="text-xl font-semibold text-stone-900">BagDrop context</h2>
            <div className="mt-5 space-y-4 text-sm leading-7 text-stone-600">
              <p>
                This page keeps the traffic and context inside BagDrop first. Users can inspect the markdown path,
                compare the listing against similar inventory, and only then click out to the marketplace.
              </p>
              <p>
                For luxury resale, the market view is often more valuable than a single listing. The linked market
                page shows whether this ask is actually attractive relative to the current supply.
              </p>
            </div>
          </section>
        </div>

        <div className="mt-8">
          <ReportListingCard listingId={listing.id} />
        </div>

        {relatedListings.length > 0 && (
          <section className="mt-10">
            <div className="mb-4 flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="mb-2 text-[11px] uppercase tracking-[0.25em] text-pink-500">Related Listings</p>
                <h2 className="text-2xl font-semibold text-stone-900">More {listing.brand} {displayModel}</h2>
              </div>
              <Link href={marketPath} className="text-sm text-stone-500 transition-colors hover:text-stone-900">
                Open market page
              </Link>
            </div>

            <div className="grid grid-cols-1 gap-5 md:grid-cols-2 xl:grid-cols-3">
              {relatedListings.map((item) => (
                <ListingCard key={item.id} listing={item} />
              ))}
            </div>
          </section>
        )}
      </main>
    </div>
  )
}
