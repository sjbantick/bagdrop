import Link from 'next/link'
import Header from '@/components/Header'
import ArbitrageRadar from '@/components/ArbitrageRadar'
import BagIndexBoard from '@/components/BagIndexBoard'
import NewDropsRadar from '@/components/NewDropsRadar'
import StructuredData from '@/components/StructuredData'
import { fetchApi } from '@/lib/api'
import { absoluteUrl } from '@/lib/site'

async function getBrief() {
  try {
    return await fetchApi('/api/intelligence/brief')
  } catch {
    return {
      generated_at: null,
      arbitrage: [],
      new_drops: [],
      bag_index_movers: [],
    }
  }
}

export const metadata = {
  title: 'BagDrop Intelligence Brief',
  description: 'A combined view of the strongest arbitrage, new-drop, and brand-level price-health signals inside BagDrop.',
  alternates: {
    canonical: '/intel',
  },
  openGraph: {
    title: 'BagDrop Intelligence Brief',
    description: 'A combined view of the strongest arbitrage, new-drop, and brand-level price-health signals inside BagDrop.',
    url: '/intel',
    type: 'article',
    images: [
      {
        url: absoluteUrl('/intel/opengraph-image'),
        width: 1200,
        height: 630,
        alt: 'BagDrop intelligence brief',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'BagDrop Intelligence Brief',
    description: 'A combined view of the strongest arbitrage, new-drop, and brand-level price-health signals inside BagDrop.',
    images: [absoluteUrl('/intel/opengraph-image')],
  },
}

export default async function IntelligenceBriefPage() {
  const brief = await getBrief()

  return (
    <div className="min-h-screen bg-[#f7f4ef]">
      <StructuredData
        data={{
          '@context': 'https://schema.org',
          '@type': 'Report',
          name: 'BagDrop Intelligence Brief',
          description: 'A combined view of arbitrage opportunities, high-signal new drops, and BagIndex movers.',
          url: absoluteUrl('/intel'),
          dateModified: brief.generated_at || undefined,
          publisher: {
            '@type': 'Organization',
            name: 'BagDrop',
          },
        }}
      />
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-6 sm:py-8">
        <section className="rounded-3xl border border-stone-200 bg-[#f4eee6] p-5 md:p-8">
          <p className="text-[11px] uppercase tracking-[0.3em] text-red-500 mb-3">BagDrop Intelligence</p>
          <h1 className="text-3xl font-semibold text-stone-950 sm:text-4xl md:text-5xl">Daily market brief</h1>
          <p className="mt-4 max-w-3xl text-base md:text-lg leading-8 text-stone-600">
            Cross-platform arbitrage opportunities, high-signal new drops, and brand-level resale pressure — updated daily.
          </p>
          {brief.generated_at && (
            <p className="mt-4 text-xs font-mono text-stone-500">
              Generated {new Date(brief.generated_at).toLocaleString()}
            </p>
          )}
        </section>

        {/* Quick links to intel sub-pages */}
        <div className="mt-8 mb-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
          <Link
            href="/intel/weekly-drops"
            className="rounded-2xl border border-stone-200 bg-white p-5 shadow-[0_4px_16px_rgba(194,168,140,0.06)] transition-all hover:border-pink-300 hover:shadow-[0_6px_24px_rgba(236,72,153,0.08)]"
          >
            <p className="text-[11px] uppercase tracking-[0.25em] text-pink-500">Report</p>
            <p className="mt-2 text-lg font-semibold text-stone-900">Weekly drops</p>
            <p className="mt-1 text-sm text-stone-500">Week-by-week summary of price drops across all brands.</p>
          </Link>
          <Link
            href="/intel/retail-prices"
            className="rounded-2xl border border-stone-200 bg-white p-5 shadow-[0_4px_16px_rgba(194,168,140,0.06)] transition-all hover:border-pink-300 hover:shadow-[0_6px_24px_rgba(236,72,153,0.08)]"
          >
            <p className="text-[11px] uppercase tracking-[0.25em] text-pink-500">Tracker</p>
            <p className="mt-2 text-lg font-semibold text-stone-900">Retail price increases</p>
            <p className="mt-1 text-sm text-stone-500">Every Chanel, Hermès, and LV retail price hike since 2019.</p>
          </Link>
          <div className="rounded-2xl border border-dashed border-stone-300 bg-stone-50/50 p-5">
            <p className="text-[11px] uppercase tracking-[0.25em] text-stone-400">Coming soon</p>
            <p className="mt-2 text-lg font-semibold text-stone-400">Cross-platform arbitrage</p>
            <p className="mt-1 text-sm text-stone-400">Same bag, different price — find the gap.</p>
          </div>
        </div>

        <div>
          <ArbitrageRadar opportunities={brief.arbitrage} />
          <NewDropsRadar opportunities={brief.new_drops} />
          <BagIndexBoard snapshots={brief.bag_index_movers} />
        </div>
      </main>
    </div>
  )
}
