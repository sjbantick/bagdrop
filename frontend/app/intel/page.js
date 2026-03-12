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

      <main className="max-w-7xl mx-auto px-4 py-8">
        <section className="rounded-3xl border border-stone-200 bg-[#f4eee6] p-6 md:p-8">
          <p className="text-[11px] uppercase tracking-[0.3em] text-red-500 mb-3">BagDrop Intelligence</p>
          <h1 className="text-4xl md:text-5xl font-semibold text-stone-950">Daily market brief</h1>
          <p className="mt-4 max-w-3xl text-base md:text-lg leading-8 text-stone-600">
            A shareable owned surface for the best BagDrop signals: mispriced listings, meaningful new drops, and brand-level
            resale pressure.
          </p>
          {brief.generated_at && (
            <p className="mt-4 text-xs font-mono text-stone-500">
              Generated {new Date(brief.generated_at).toLocaleString()}
            </p>
          )}
        </section>

        <div className="mt-8">
          <ArbitrageRadar opportunities={brief.arbitrage} />
          <NewDropsRadar opportunities={brief.new_drops} />
          <BagIndexBoard snapshots={brief.bag_index_movers} />
        </div>
      </main>
    </div>
  )
}
