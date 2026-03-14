import Link from 'next/link'
import Header from '@/components/Header'
import { fetchApi } from '@/lib/api'
import { formatCurrency, titleCase } from '@/lib/format'
import { absoluteUrl } from '@/lib/site'

export const metadata = {
  title: 'Condition Price Guide | BagDrop',
  description:
    'How much does bag condition affect resale price? See condition premiums across Chanel, Hermès, Louis Vuitton and more — updated from live market data.',
  alternates: { canonical: '/intel/condition-guide' },
  openGraph: {
    title: 'Condition Price Guide | BagDrop',
    description: 'How much does bag condition affect resale price? Live condition premiums across top luxury markets.',
    url: '/intel/condition-guide',
    type: 'article',
    images: [{ url: absoluteUrl('/intel/opengraph-image'), width: 1200, height: 630, alt: 'BagDrop condition price guide' }],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Condition Price Guide | BagDrop',
    description: 'How much does bag condition affect resale price? Live data from BagDrop.',
    images: [absoluteUrl('/intel/opengraph-image')],
  },
}

const CONDITION_ORDER = ['pristine', 'excellent', 'good', 'fair']

const CONDITION_DESCRIPTIONS = {
  pristine: 'Never used or worn, essentially new with all original materials.',
  excellent: 'Like new with minimal signs of use. Clean interior, no visible wear.',
  good: 'Some minor wear consistent with light use. Functional and presentable.',
  fair: 'Visible wear. May have scuffs, marks, or hardware tarnish but remains wearable.',
}

function AdjustmentBadge({ pct }) {
  if (pct == null) return null
  const abs = Math.abs(pct).toFixed(1)
  if (pct >= 2) return (
    <span className="inline-flex rounded-full border border-amber-200 bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700">
      +{abs}% vs avg
    </span>
  )
  if (pct <= -2) return (
    <span className="inline-flex rounded-full border border-green-200 bg-green-50 px-2.5 py-0.5 text-xs font-medium text-green-700">
      -{abs}% vs avg
    </span>
  )
  return (
    <span className="inline-flex rounded-full border border-stone-200 bg-stone-50 px-2.5 py-0.5 text-xs font-medium text-stone-500">
      at avg
    </span>
  )
}

async function getConditionGuide() {
  try {
    return await fetchApi('/api/intel/condition-guide')
  } catch {
    return null
  }
}

export default async function ConditionGuidePage() {
  const data = await getConditionGuide()

  const sortedPremiums = data?.condition_premiums
    ? [...data.condition_premiums].sort(
        (a, b) => CONDITION_ORDER.indexOf(a.condition) - CONDITION_ORDER.indexOf(b.condition)
      )
    : []

  return (
    <div className="min-h-screen bg-[#fffdf8]">
      <Header />

      <main className="mx-auto max-w-5xl px-4 py-6 sm:py-8">
        <div className="flex flex-wrap items-center gap-2 text-sm text-stone-500 mb-6">
          <Link href="/intel" className="transition-colors hover:text-stone-900">Intel</Link>
          <span>/</span>
          <span className="text-stone-700">Condition Guide</span>
        </div>

        <section className="mb-10">
          <p className="mb-2 text-[11px] uppercase tracking-[0.25em] text-pink-500">Price Intelligence</p>
          <h1 className="text-3xl font-semibold text-stone-900 sm:text-4xl">Condition price guide</h1>
          <p className="mt-3 max-w-3xl text-sm leading-7 text-stone-600">
            Condition grade is the single biggest variable in resale pricing after brand and model. This guide shows
            how much each condition tier commands above or below the market average — based on live BagDrop data
            across the top-traded markets.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="mb-4 text-lg font-semibold text-stone-900">Condition grades</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            {CONDITION_ORDER.map((condition) => {
              const premium = sortedPremiums.find((p) => p.condition === condition)
              return (
                <div key={condition} className="rounded-2xl border border-stone-200 bg-white p-5 shadow-[0_4px_16px_rgba(194,168,140,0.06)]">
                  <div className="flex items-center justify-between gap-3 mb-2">
                    <h3 className="text-base font-semibold text-stone-900">{titleCase(condition)}</h3>
                    {premium && <AdjustmentBadge pct={premium.avg_adjustment_pct} />}
                  </div>
                  <p className="text-sm leading-6 text-stone-500">{CONDITION_DESCRIPTIONS[condition]}</p>
                  {premium && (
                    <div className="mt-3 flex items-center gap-4 text-sm">
                      <span className="text-stone-400">Avg price</span>
                      <span className="font-semibold text-stone-900">{formatCurrency(premium.avg_price)}</span>
                      <span className="text-stone-400">{premium.listing_count} listings</span>
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </section>

        {data && data.per_market && data.per_market.length > 0 && (
          <section className="mb-10">
            <div className="mb-4 flex items-end justify-between">
              <h2 className="text-lg font-semibold text-stone-900">Per-market breakdown</h2>
              <p className="text-xs text-stone-400">{data.total_listings_analyzed.toLocaleString()} listings analyzed</p>
            </div>

            <div className="space-y-4">
              {data.per_market.map((market) => {
                const orderedConditions = [...market.conditions].sort(
                  (a, b) => CONDITION_ORDER.indexOf(a.condition) - CONDITION_ORDER.indexOf(b.condition)
                )
                return (
                  <div key={market.canonical_path} className="rounded-2xl border border-stone-200 bg-white p-5">
                    <Link
                      href={market.canonical_path}
                      className="text-base font-semibold text-stone-900 hover:text-pink-600 transition-colors"
                    >
                      {market.brand} {titleCase(market.model)}
                    </Link>

                    <div className="mt-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
                      {orderedConditions.map((c) => (
                        <div key={c.condition} className="rounded-xl border border-stone-100 bg-[#fffaf2] px-3 py-2.5">
                          <p className="text-[11px] uppercase tracking-[0.2em] text-stone-400">{titleCase(c.condition)}</p>
                          <p className="mt-1 text-sm font-semibold text-stone-900">{formatCurrency(c.avg_price)}</p>
                          <div className="mt-1">
                            <AdjustmentBadge pct={c.adjustment_pct} />
                          </div>
                          <p className="mt-1 text-[11px] text-stone-400">{c.listing_count} listings</p>
                        </div>
                      ))}
                    </div>
                  </div>
                )
              })}
            </div>
          </section>
        )}

        {(!data || !data.per_market || data.per_market.length === 0) && (
          <div className="rounded-2xl border border-stone-200 bg-stone-50 p-8 text-center">
            <p className="text-sm text-stone-500">Condition data is still accumulating — check back once more listings have been tracked.</p>
          </div>
        )}

        <section className="rounded-2xl border border-stone-200 bg-[#fffaf2] p-5">
          <p className="text-[11px] uppercase tracking-[0.25em] text-pink-500 mb-2">How to use this</p>
          <p className="text-sm leading-7 text-stone-600">
            Premiums are computed from the average asking price for each condition tier vs the overall market average for that
            brand and model. A listing priced below the average for its condition is typically a strong buy. A &ldquo;Good&rdquo; bag
            priced at &ldquo;Excellent&rdquo; rates is worth scrutinizing before purchasing.
          </p>
          {data?.generated_at && (
            <p className="mt-3 text-xs font-mono text-stone-400">
              Data as of {new Date(data.generated_at).toLocaleString()}
            </p>
          )}
        </section>
      </main>
    </div>
  )
}
