'use client'

import { formatCurrency, formatPercent, platformLabel } from '@/lib/format'

export default function PlatformCompare({ comparison }) {
  if (!comparison || !comparison.platforms || comparison.platforms.length < 2) {
    return null
  }

  const maxAvgPrice = Math.max(...comparison.platforms.map((p) => p.avg_price))

  return (
    <section className="mt-8">
      <div className="rounded-3xl border border-stone-200 bg-[#f7f1e8] p-5 shadow-[0_12px_40px_rgba(206,182,150,0.10)] md:p-8">
        <p className="mb-2 text-[11px] uppercase tracking-[0.3em] text-pink-500">
          Cross-Platform Comparison
        </p>
        <h2 className="text-2xl font-semibold text-stone-900 sm:text-3xl">
          {comparison.brand} {comparison.model}
        </h2>
        <p className="mt-2 text-base text-stone-600">
          {comparison.total_listings} listings across {comparison.platforms.length} platforms
        </p>

        {comparison.price_spread > 0 && (
          <div className="mt-5 rounded-2xl border border-pink-200 bg-pink-50/80 px-5 py-4">
            <p className="text-lg font-semibold text-pink-700 sm:text-xl">
              Save up to {formatCurrency(comparison.price_spread)} by comparing platforms
            </p>
            <p className="mt-1 text-sm text-pink-600/80">
              {formatPercent(comparison.price_spread_pct)} price spread between the cheapest and most
              expensive average asking price
            </p>
          </div>
        )}

        <div className="mt-6 space-y-3">
          {comparison.platforms.map((platform) => {
            const barWidth = maxAvgPrice > 0 ? (platform.avg_price / maxAvgPrice) * 100 : 0
            const isBestValue = platform.platform === comparison.best_value_platform
            const isCheapest = platform.platform === comparison.cheapest_platform

            return (
              <div
                key={platform.platform}
                className={`rounded-2xl border bg-white/80 p-4 transition-colors ${
                  isBestValue
                    ? 'border-green-300 ring-1 ring-green-200'
                    : 'border-stone-200'
                }`}
              >
                <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-base font-semibold text-stone-900">
                      {platformLabel(platform.platform)}
                    </span>
                    <span className="rounded-full border border-stone-300 bg-[#fffaf2] px-2.5 py-0.5 text-xs font-mono text-stone-600">
                      {platform.listing_count} listings
                    </span>
                    {isBestValue && (
                      <span className="rounded-full border border-green-300 bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700">
                        Best Value
                      </span>
                    )}
                    {isCheapest && !isBestValue && (
                      <span className="rounded-full border border-pink-300 bg-pink-50 px-2.5 py-0.5 text-xs font-medium text-pink-600">
                        Lowest Price
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-4 text-sm">
                    <div className="text-right">
                      <p className="text-[11px] uppercase tracking-[0.2em] text-stone-400">Low</p>
                      <p className="font-semibold text-stone-900">
                        {formatCurrency(platform.lowest_price)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-[11px] uppercase tracking-[0.2em] text-stone-400">Avg</p>
                      <p className="font-semibold text-stone-900">
                        {formatCurrency(platform.avg_price)}
                      </p>
                    </div>
                    {platform.best_drop_pct != null && platform.best_drop_pct > 0 && (
                      <div className="text-right">
                        <p className="text-[11px] uppercase tracking-[0.2em] text-stone-400">
                          Drop
                        </p>
                        <p className="font-semibold text-pink-600">
                          -{formatPercent(platform.best_drop_pct)}
                        </p>
                      </div>
                    )}
                    {platform.value_score != null && (
                      <div className="text-right">
                        <p className="text-[11px] uppercase tracking-[0.2em] text-stone-400">
                          Score
                        </p>
                        <p
                          className={`font-mono font-semibold ${
                            platform.value_score >= 80
                              ? 'text-green-600'
                              : platform.value_score >= 50
                                ? 'text-amber-600'
                                : 'text-stone-600'
                          }`}
                        >
                          {platform.value_score}
                        </p>
                      </div>
                    )}
                  </div>
                </div>

                <div className="mt-3">
                  <div className="h-3 w-full overflow-hidden rounded-full bg-stone-100">
                    <div
                      className={`h-full rounded-full transition-all ${
                        isBestValue
                          ? 'bg-gradient-to-r from-green-400 to-green-500'
                          : isCheapest
                            ? 'bg-gradient-to-r from-pink-400 to-pink-500'
                            : 'bg-gradient-to-r from-stone-300 to-stone-400'
                      }`}
                      style={{ width: `${barWidth}%` }}
                    />
                  </div>
                </div>
              </div>
            )
          })}
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-3 text-xs text-stone-500">
          <span>
            Overall lowest:{' '}
            <span className="font-semibold text-stone-900">
              {formatCurrency(comparison.overall_lowest_price)}
            </span>
          </span>
          <span className="text-stone-300">|</span>
          <span>
            Cheapest platform:{' '}
            <span className="font-semibold text-stone-900">
              {platformLabel(comparison.cheapest_platform)}
            </span>
          </span>
          {comparison.best_value_platform &&
            comparison.best_value_platform !== comparison.cheapest_platform && (
              <>
                <span className="text-stone-300">|</span>
                <span>
                  Best value:{' '}
                  <span className="font-semibold text-stone-900">
                    {platformLabel(comparison.best_value_platform)}
                  </span>
                </span>
              </>
            )}
        </div>
      </div>
    </section>
  )
}
