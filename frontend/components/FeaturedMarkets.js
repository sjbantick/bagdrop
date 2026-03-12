import Link from 'next/link'
import { formatCurrency, formatPercent, titleCase } from '@/lib/format'

export default function FeaturedMarkets({ markets = [] }) {
  if (!markets.length) {
    return null
  }

  return (
    <section className="mb-8">
      <div className="flex items-end justify-between gap-4 mb-4">
        <div>
          <p className="text-[11px] uppercase tracking-[0.25em] text-red-500 mb-2">Market Pages</p>
          <h2 className="text-2xl font-semibold text-white">Most active handbag markets</h2>
        </div>
        <p className="text-sm text-gray-500 max-w-md text-right hidden md:block">
          Canonical pages BagDrop can rank and share instead of dropping users straight onto marketplace inventory.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {markets.map((market) => (
          <Link
            key={market.canonical_path}
            href={market.canonical_path}
            className="group rounded-2xl border border-gray-800 bg-gradient-to-br from-gray-950 via-gray-900 to-black p-5 transition-colors hover:border-red-500"
          >
            <div className="flex items-start justify-between gap-4">
              <div>
                <p className="text-sm font-medium text-gray-400">{market.brand}</p>
                <h3 className="mt-1 text-xl font-semibold text-white group-hover:text-red-400">
                  {titleCase(market.model)}
                </h3>
              </div>
              <div className="rounded-full border border-red-500/40 bg-red-500/10 px-3 py-1 text-xs font-mono text-red-300">
                {market.listing_count} live
              </div>
            </div>

            <div className="mt-6 grid grid-cols-3 gap-3 text-sm">
              <div>
                <p className="text-gray-500">Lowest ask</p>
                <p className="mt-1 font-semibold text-white">{formatCurrency(market.lowest_price)}</p>
              </div>
              <div>
                <p className="text-gray-500">Avg drop</p>
                <p className="mt-1 font-semibold text-red-400">
                  {market.average_drop_pct ? `-${formatPercent(market.average_drop_pct)}` : 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-gray-500">Best drop</p>
                <p className="mt-1 font-semibold text-red-500">
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
