import Link from 'next/link'
import { notFound } from 'next/navigation'
import Header from '@/components/Header'
import { fetchApi } from '@/lib/api'
import { formatCurrency, formatPercent, titleCase } from '@/lib/format'

async function getBrandMarkets(brandSlug) {
  try {
    const all = await fetchApi('/api/markets/featured?limit=48&min_listings=1')
    // Find the canonical brand name by matching slug
    const { slugifyValue } = await import('@/lib/slug')
    return (all || []).filter((m) => slugifyValue(m.brand) === brandSlug)
  } catch {
    return []
  }
}

export async function generateMetadata({ params }) {
  const markets = await getBrandMarkets(params.brand)
  if (!markets.length) return { title: 'Brand Not Found | BagDrop' }

  const brand = markets[0].brand
  const totalListings = markets.reduce((sum, m) => sum + m.listing_count, 0)
  const biggestDrop = Math.max(...markets.map((m) => m.biggest_drop_pct || 0))

  return {
    title: `${brand} resale prices | BagDrop`,
    description: `${totalListings} live ${brand} listings across ${markets.length} models${biggestDrop > 0 ? ` — up to -${biggestDrop.toFixed(1)}% off` : ''} on Fashionphile, Rebag, The RealReal, Vestiaire, and more.`,
    alternates: { canonical: `/${params.brand}` },
  }
}

export default async function BrandPage({ params }) {
  const markets = await getBrandMarkets(params.brand)
  if (!markets.length) notFound()

  const brand = markets[0].brand
  const totalListings = markets.reduce((sum, m) => sum + m.listing_count, 0)
  const sortedMarkets = [...markets].sort((a, b) => b.listing_count - a.listing_count)

  return (
    <div className="min-h-screen bg-[#fffdf8]">
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-6 sm:py-8">
        <div className="flex flex-wrap items-center gap-2 text-sm text-stone-500 mb-6">
          <Link href="/markets" className="transition-colors hover:text-stone-900">Markets</Link>
          <span>/</span>
          <span className="text-stone-700">{brand}</span>
        </div>

        <div className="mb-8">
          <p className="mb-2 text-[11px] uppercase tracking-[0.25em] text-pink-500">Brand</p>
          <h1 className="text-3xl font-semibold text-stone-900 sm:text-4xl">{brand}</h1>
          <p className="mt-3 text-sm leading-7 text-stone-600">
            {totalListings.toLocaleString()} live listings across {markets.length} {brand} models tracked by BagDrop.
          </p>
        </div>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
          {sortedMarkets.map((market) => {
            const displayModel = titleCase(market.model)
            return (
              <Link
                key={market.canonical_path}
                href={market.canonical_path}
                className="group rounded-2xl border border-stone-200 bg-white p-4 shadow-[0_4px_16px_rgba(194,168,140,0.08)] transition-all hover:border-pink-300 hover:shadow-[0_6px_24px_rgba(236,72,153,0.08)]"
              >
                <p className="text-base font-semibold text-stone-900 group-hover:text-pink-600 leading-snug">
                  {displayModel}
                </p>

                <div className="mt-3 flex items-end justify-between">
                  <div>
                    <p className="text-[11px] text-stone-400">Listings</p>
                    <p className="text-lg font-bold text-stone-900">{market.listing_count}</p>
                  </div>
                  {market.lowest_price && (
                    <div className="text-right">
                      <p className="text-[11px] text-stone-400">From</p>
                      <p className="text-base font-semibold text-stone-900">{formatCurrency(market.lowest_price)}</p>
                    </div>
                  )}
                </div>

                {market.biggest_drop_pct && (
                  <div className="mt-3 rounded-full bg-pink-50 border border-pink-100 px-3 py-1 text-xs font-medium text-pink-600 inline-block">
                    up to -{formatPercent(market.biggest_drop_pct)} off
                  </div>
                )}
              </Link>
            )
          })}
        </div>
      </main>
    </div>
  )
}
