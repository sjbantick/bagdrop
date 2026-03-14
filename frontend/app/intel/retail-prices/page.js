import Link from 'next/link'
import Header from '@/components/Header'
import { formatCurrency } from '@/lib/format'
import { RETAIL_PRICE_HISTORY, computeRetailStats } from '@/lib/retail-prices'

export const metadata = {
  title: 'Retail Price Increase Tracker | BagDrop',
  description:
    'Track every Chanel, Hermès, and Louis Vuitton retail price increase since 2019. See how much luxury handbag prices have risen at retail vs resale.',
  alternates: { canonical: '/intel/retail-prices' },
}

function PriceTimeline({ history }) {
  return (
    <div className="mt-4 space-y-2">
      {history.map((point, i) => {
        const prev = i > 0 ? history[i - 1] : null
        const increase = prev ? point.price - prev.price : null
        const pct = prev ? ((increase / prev.price) * 100).toFixed(1) : null
        const dateLabel = new Date(point.date + 'T00:00:00').toLocaleDateString('en-US', {
          year: 'numeric',
          month: 'short',
        })

        return (
          <div key={point.date} className="flex items-center gap-3">
            <div className="flex w-20 shrink-0 items-center text-xs text-stone-400">{dateLabel}</div>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-stone-900">{formatCurrency(point.price)}</span>
              {increase > 0 && (
                <span className="rounded-full border border-pink-100 bg-pink-50 px-2 py-0.5 text-[11px] font-medium text-pink-600">
                  +{formatCurrency(increase)} ({pct}%)
                </span>
              )}
              {point.event && (
                <span className="text-[11px] text-stone-400">{point.event}</span>
              )}
            </div>
          </div>
        )
      })}
    </div>
  )
}

export default function RetailPricesPage() {
  const entries = RETAIL_PRICE_HISTORY.map(computeRetailStats)

  // Group by brand
  const brands = {}
  for (const entry of entries) {
    if (!brands[entry.brand]) brands[entry.brand] = []
    brands[entry.brand].push(entry)
  }

  // Sort brands: Chanel first (most increases), then alphabetical
  const brandOrder = Object.keys(brands).sort((a, b) => {
    if (a === 'Chanel') return -1
    if (b === 'Chanel') return 1
    return a.localeCompare(b)
  })

  // Top-level stats
  const avgTotalIncrease = Math.round(
    entries.reduce((sum, e) => sum + e.totalIncreasePct, 0) / entries.length
  )
  const maxIncrease = entries.reduce((max, e) => (e.totalIncreasePct > max.totalIncreasePct ? e : max), entries[0])

  return (
    <div className="min-h-screen bg-[#fffdf8]">
      <Header />

      <main className="mx-auto max-w-5xl px-4 py-6 sm:py-8">
        <div className="flex flex-wrap items-center gap-2 text-sm text-stone-500 mb-6">
          <Link href="/intel" className="transition-colors hover:text-stone-900">Intel</Link>
          <span>/</span>
          <span className="text-stone-700">Retail Prices</span>
        </div>

        <section className="mb-10">
          <p className="mb-2 text-[11px] uppercase tracking-[0.25em] text-pink-500">Price Intelligence</p>
          <h1 className="text-3xl font-semibold text-stone-900 sm:text-4xl">
            Retail price increase tracker
          </h1>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-stone-600">
            Luxury brands raise retail prices 1–3 times per year, compounding the cost of waiting.
            This tracker logs every confirmed increase since 2019 for Chanel, Hermès, and Louis Vuitton
            so you can see how much prices have risen — and whether resale is actually a deal.
          </p>
        </section>

        {/* Summary cards */}
        <div className="mb-10 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <div className="rounded-2xl border border-stone-200 bg-[#f7f1e8] p-5">
            <p className="text-sm text-stone-500">Bags tracked</p>
            <p className="mt-2 text-3xl font-semibold text-stone-900">{entries.length}</p>
            <p className="mt-1 text-xs text-stone-400">across {brandOrder.length} brands</p>
          </div>
          <div className="rounded-2xl border border-stone-200 bg-[#f7f1e8] p-5">
            <p className="text-sm text-stone-500">Avg total increase</p>
            <p className="mt-2 text-3xl font-semibold text-pink-600">+{avgTotalIncrease}%</p>
            <p className="mt-1 text-xs text-stone-400">since 2019</p>
          </div>
          <div className="rounded-2xl border border-stone-200 bg-[#f7f1e8] p-5">
            <p className="text-sm text-stone-500">Biggest increase</p>
            <p className="mt-2 text-3xl font-semibold text-pink-700">+{maxIncrease.totalIncreasePct}%</p>
            <p className="mt-1 text-xs text-stone-400">
              {maxIncrease.brand} {maxIncrease.model}
            </p>
          </div>
        </div>

        {/* Brand sections */}
        {brandOrder.map((brand) => (
          <section key={brand} className="mb-12">
            <h2 className="mb-6 text-2xl font-semibold text-stone-900">{brand}</h2>
            <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
              {brands[brand].map((entry) => (
                <div
                  key={`${entry.brand}-${entry.model}`}
                  className="rounded-2xl border border-stone-200 bg-white p-5 shadow-[0_4px_16px_rgba(194,168,140,0.06)]"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <h3 className="text-lg font-semibold text-stone-900">{entry.model}</h3>
                      {entry.size !== 'One Size' && (
                        <p className="text-xs text-stone-400">Size {entry.size}</p>
                      )}
                    </div>
                    <div className="text-right">
                      <p className="text-xl font-semibold text-stone-900">{formatCurrency(entry.currentRetail)}</p>
                      <p className="text-xs text-stone-400">current retail</p>
                    </div>
                  </div>

                  <div className="mt-4 flex gap-4">
                    <div className="rounded-full border border-pink-100 bg-pink-50 px-3 py-1 text-xs font-medium text-pink-600">
                      +{entry.totalIncreasePct}% total
                    </div>
                    <div className="rounded-full border border-stone-200 bg-stone-50 px-3 py-1 text-xs font-medium text-stone-600">
                      ~{entry.annualizedPct}%/yr
                    </div>
                    <div className="rounded-full border border-stone-200 bg-stone-50 px-3 py-1 text-xs font-medium text-stone-600">
                      {entry.increaseCount} increases
                    </div>
                  </div>

                  <PriceTimeline history={entry.history} />
                </div>
              ))}
            </div>
          </section>
        ))}

        {/* Editorial note */}
        <section className="rounded-2xl border border-stone-200 bg-[#fffaf2] p-5">
          <p className="text-[11px] uppercase tracking-[0.25em] text-pink-500 mb-2">Note</p>
          <p className="text-sm leading-7 text-stone-600">
            Retail prices shown are for standard leather/canvas variants in USD at US boutiques.
            Exotic leather, limited editions, and regional pricing may differ. Prices are sourced
            from brand websites, PurseBlog archives, and community-confirmed data points.
            BagDrop updates this tracker when brands announce or implement price changes.
          </p>
        </section>
      </main>
    </div>
  )
}
