import Link from 'next/link'
import { formatCurrency, formatPercent, platformLabel, titleCase } from '@/lib/format'

export default function ArbitrageRadar({ opportunities = [] }) {
  if (!opportunities.length) {
    return null
  }

  return (
    <section className="mb-8">
      <div className="flex items-end justify-between gap-4 mb-4">
        <div>
          <p className="text-[11px] uppercase tracking-[0.25em] text-red-500 mb-2">Arbitrage Radar</p>
          <h2 className="text-2xl font-semibold text-stone-950">Listings mispriced versus their live market</h2>
        </div>
        <p className="text-sm text-stone-500 max-w-md text-right hidden md:block">
          This is the first real BagDrop intelligence layer: same-model listings that are materially below their live
          market average across platforms.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        {opportunities.map((opportunity) => {
          const listing = opportunity.listing
          const detailPath = `/listings/${listing.id}`
          return (
            <Link
              key={listing.id}
              href={detailPath}
              className="group rounded-2xl border border-stone-200 bg-[#f4eee6] p-5 transition-colors hover:border-pink-400"
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-stone-500">{listing.brand}</p>
                  <h3 className="mt-1 text-lg font-semibold text-stone-950 group-hover:text-pink-600 sm:text-xl">
                    {titleCase(listing.model)}
                  </h3>
                  <p className="mt-2 text-xs font-mono text-stone-500">{platformLabel(listing.platform)}</p>
                </div>
                <div className="w-fit shrink-0 rounded-full border border-pink-300 bg-pink-50 px-3 py-1 text-xs font-mono text-pink-600">
                  {opportunity.market_gap_pct}% below avg
                </div>
              </div>

              <div className="mt-6 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
                <div>
                  <p className="text-stone-500">Current ask</p>
                  <p className="mt-1 font-semibold text-stone-950">{formatCurrency(listing.current_price)}</p>
                </div>
                <div>
                  <p className="text-stone-500">Market avg</p>
                  <p className="mt-1 font-semibold text-stone-950">{formatCurrency(opportunity.market_average_price)}</p>
                </div>
                <div>
                  <p className="text-stone-500">Gap</p>
                  <p className="mt-1 font-semibold text-pink-600">-{formatCurrency(opportunity.market_gap_amount)}</p>
                </div>
                <div>
                  <p className="text-stone-500">Listings</p>
                  <p className="mt-1 font-semibold text-stone-950">
                    {opportunity.market_listing_count} across {opportunity.market_platform_count} platforms
                  </p>
                </div>
              </div>

              <div className="mt-5 flex flex-col gap-2 border-t border-stone-200 pt-4 text-xs sm:flex-row sm:items-center sm:justify-between">
                <span className="text-stone-500">
                  Listing drop: <span className="text-pink-600">-{formatPercent(listing.drop_pct)}</span>
                </span>
                <span className="text-stone-500">Open listing</span>
              </div>
            </Link>
          )
        })}
      </div>
    </section>
  )
}
