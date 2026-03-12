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
          <p className="mb-2 text-[11px] uppercase tracking-[0.25em] text-pink-500">New Drops</p>
          <h2 className="text-2xl font-semibold text-stone-900">Fresh listings that matter right now</h2>
        </div>
        <p className="hidden max-w-md text-right text-sm text-stone-500 md:block">
          Fresh listings ranked by urgency, markdown strength, and market context instead of raw chronology.
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 xl:grid-cols-3">
        {opportunities.map((opportunity) => {
          const listing = opportunity.listing
          return (
            <Link
              key={listing.id}
              href={`/listings/${listing.id}`}
              className="group rounded-2xl border border-stone-200 bg-[#fffaf2] p-5 shadow-[0_10px_30px_rgba(194,168,140,0.08)] transition-colors hover:border-pink-300"
            >
              <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <p className="text-sm font-medium text-stone-500">{listing.brand}</p>
                  <h3 className="mt-1 text-lg font-semibold text-stone-900 group-hover:text-pink-500 sm:text-xl">
                    {titleCase(listing.model)}
                  </h3>
                  <p className="mt-2 text-xs font-mono text-stone-500">{platformLabel(listing.platform)}</p>
                </div>
                <div className="w-fit shrink-0 rounded-full border border-pink-300 bg-pink-50 px-3 py-1 text-xs font-mono text-pink-600">
                  {opportunity.significance_score} score
                </div>
              </div>

              <div className="mt-6 grid grid-cols-1 gap-3 text-sm sm:grid-cols-2">
                <div>
                  <p className="text-stone-500">Current ask</p>
                  <p className="mt-1 font-semibold text-stone-900">{formatCurrency(listing.current_price)}</p>
                </div>
                <div>
                  <p className="text-stone-500">Drop</p>
                  <p className="mt-1 font-semibold text-pink-600">-{formatPercent(listing.drop_pct)}</p>
                </div>
                <div>
                  <p className="text-stone-500">Age</p>
                  <p className="mt-1 font-semibold text-stone-900">{opportunity.hours_since_first_seen}h</p>
                </div>
                <div>
                  <p className="text-stone-500">Below market</p>
                  <p className="mt-1 font-semibold text-pink-600">
                    {opportunity.market_gap_pct ? `-${opportunity.market_gap_pct}%` : 'N/A'}
                  </p>
                </div>
              </div>

              <div className="mt-5 flex flex-col gap-2 border-t border-stone-200 pt-4 text-xs sm:flex-row sm:items-center sm:justify-between">
                <span className="text-stone-500">{opportunity.market_platform_count} platforms in market</span>
                <span className="text-stone-500">See why it matters</span>
              </div>
            </Link>
          )
        })}
      </div>
    </section>
  )
}
