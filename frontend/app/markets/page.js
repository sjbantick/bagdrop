import Link from 'next/link'
import Header from '@/components/Header'
import { fetchApi } from '@/lib/api'
import { formatCurrency, formatPercent, titleCase } from '@/lib/format'

export const metadata = {
  title: 'All Markets | BagDrop',
  description: 'Browse every luxury handbag brand and model tracked by BagDrop — live resale prices, markdowns, and market comparisons.',
  alternates: { canonical: '/markets' },
}

async function getAllMarkets() {
  try {
    return await fetchApi('/api/markets/featured?limit=48&min_listings=1')
  } catch {
    return []
  }
}

export default async function MarketsIndexPage() {
  const markets = await getAllMarkets()

  // Group by brand
  const byBrand = {}
  for (const market of markets) {
    if (!byBrand[market.brand]) byBrand[market.brand] = []
    byBrand[market.brand].push(market)
  }
  const brands = Object.keys(byBrand).sort()

  return (
    <div className="min-h-screen bg-[#fffdf8]">
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-6 sm:py-8">
        <div className="mb-8">
          <p className="mb-2 text-[11px] uppercase tracking-[0.25em] text-pink-500">Browse</p>
          <h1 className="text-3xl font-semibold text-stone-900 sm:text-4xl">All markets</h1>
          <p className="mt-3 text-sm leading-7 text-stone-600">
            {markets.length} brand/model markets tracked across Fashionphile, Rebag, The RealReal, Vestiaire, and more.
          </p>
        </div>

        {brands.length === 0 ? (
          <p className="text-stone-500 text-sm">Loading markets — scrapers are running, check back soon.</p>
        ) : (
          <div className="space-y-10">
            {brands.map((brand) => (
              <section key={brand}>
                <h2 className="mb-4 text-[11px] uppercase tracking-[0.3em] text-stone-500 border-b border-stone-200 pb-2">
                  {brand}
                </h2>
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                  {byBrand[brand].map((market) => {
                    const displayModel = titleCase(market.model)
                    return (
                      <Link
                        key={market.canonical_path}
                        href={market.canonical_path}
                        className="group rounded-2xl border border-stone-200 bg-white p-4 shadow-[0_4px_16px_rgba(194,168,140,0.08)] transition-all hover:border-pink-300 hover:shadow-[0_6px_24px_rgba(236,72,153,0.08)]"
                      >
                        <p className="text-[11px] uppercase tracking-[0.2em] text-stone-400">{brand}</p>
                        <p className="mt-1 text-base font-semibold text-stone-900 group-hover:text-pink-600 leading-snug">
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
              </section>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
