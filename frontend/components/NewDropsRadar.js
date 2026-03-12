import Link from 'next/link'
import { formatCurrency, formatPercent, platformLabel, titleCase } from '@/lib/format'

export default function NewDropsRadar({ opportunities = [] }) {
  if (!opportunities.length) {
    return null
  }

  return (
    <section className="mb-8">
      <div className="flex items-end justify-between gap-4 mb-4">
        <div>
          <p className="text-[11px] uppercase tracking-[0.25em] text-red-500 mb-2">New Drops</p>
          <h2 className="text-2xl font-semibold text-white">Fresh listings that matter right now</h2>
        </div>
        <p className="text-sm text-gray-500 max-w-md text-right hidden md:block">
          Ranked by freshness, markdown strength, and live market context instead of raw chronology.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
        {opportunities.map((opportunity) => {
          const listing = opportunity.listing
          return (
            <Link
              key={listing.id}
              href={`/listings/${listing.id}`}
              className="group rounded-2xl border border-gray-800 bg-gradient-to-br from-gray-950 via-gray-900 to-black p-5 transition-colors hover:border-red-500"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <p className="text-sm font-medium text-gray-400">{listing.brand}</p>
                  <h3 className="mt-1 text-xl font-semibold text-white group-hover:text-red-400">
                    {titleCase(listing.model)}
                  </h3>
                  <p className="mt-2 text-xs font-mono text-gray-500">{platformLabel(listing.platform)}</p>
                </div>
                <div className="rounded-full border border-red-500/40 bg-red-500/10 px-3 py-1 text-xs font-mono text-red-300">
                  {opportunity.significance_score} score
                </div>
              </div>

              <div className="mt-6 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-gray-500">Current ask</p>
                  <p className="mt-1 font-semibold text-white">{formatCurrency(listing.current_price)}</p>
                </div>
                <div>
                  <p className="text-gray-500">Drop</p>
                  <p className="mt-1 font-semibold text-red-300">-{formatPercent(listing.drop_pct)}</p>
                </div>
                <div>
                  <p className="text-gray-500">Age</p>
                  <p className="mt-1 font-semibold text-white">{opportunity.hours_since_first_seen}h</p>
                </div>
                <div>
                  <p className="text-gray-500">Below market</p>
                  <p className="mt-1 font-semibold text-red-400">
                    {opportunity.market_gap_pct ? `-${opportunity.market_gap_pct}%` : 'N/A'}
                  </p>
                </div>
              </div>

              <div className="mt-5 flex items-center justify-between gap-3 border-t border-gray-800 pt-4 text-xs">
                <span className="text-gray-400">{opportunity.market_platform_count} platforms in market</span>
                <span className="text-gray-500">Open listing</span>
              </div>
            </Link>
          )
        })}
      </div>
    </section>
  )
}
