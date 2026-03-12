import Link from 'next/link'
import { formatCurrency, formatPercent, titleCase } from '@/lib/format'

export default function FeaturedMarkets({ markets = [] }) {
  if (!markets.length) {
    return null
  }

  return (
    <section className="mb-8">
      <div className="mb-4 flex items-end justify-between gap-4">
        <div>
          <p className="mb-2 text-[11px] uppercase tracking-[0.25em] text-pink-500">Market Pages</p>
          <h2 className="text-2xl font-semibold text-stone-900">Most active handbag markets</h2>
        </div>
        <p className="hidden max-w-md text-right text-sm text-stone-500 md:block">
          Canonical market pages where users can compare live supply before leaving BagDrop for a marketplace listing.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {markets.map((market) => (
          <Link
            key={market.canonical_path}
            href={market.canonical_path}
            className="group rounded-2xl border border-stone-200 bg-[#f7f1e8] p-5 transition-colors hover:border-pink-300"
          >
            <div className="flex items-start justify-between gap-4">
              <div className="min-w-0">
                <p className="text-sm font-medium text-stone-500">{market.brand}</p>
                <h3 className="mt-1 text-lg font-semibold text-stone-900 group-hover:text-pink-500 sm:text-xl">
                  {titleCase(market.model)}
                </h3>
              </div>
              <div className="shrink-0 rounded-full border border-pink-300 bg-pink-50 px-3 py-1 text-xs font-mono text-pink-600">
                {market.listing_count} live
              </div>
            </div>

            <div className="mt-6 grid grid-cols-1 gap-3 text-sm sm:grid-cols-3">
              <div>
                <p className="text-stone-500">Lowest ask</p>
                <p className="mt-1 font-semibold text-stone-900">{formatCurrency(market.lowest_price)}</p>
              </div>
              <div>
                <p className="text-stone-500">Avg drop</p>
                <p className="mt-1 font-semibold text-pink-600">
                  {market.average_drop_pct ? `-${formatPercent(market.average_drop_pct)}` : 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-stone-500">Best drop</p>
                <p className="mt-1 font-semibold text-pink-700">
                  {market.biggest_drop_pct ? `-${formatPercent(market.biggest_drop_pct)}` : 'N/A'}
                </p>
              </div>
            </div>
          </Link>
        ))}
      </div>
    </section>
  )
}
