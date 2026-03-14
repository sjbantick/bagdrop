import Link from 'next/link'
import Header from '@/components/Header'
import { fetchApi } from '@/lib/api'
import { absoluteUrl } from '@/lib/site'

export const metadata = {
  title: 'Weekly Luxury Bag Drop Reports | BagDrop',
  description: 'Browse weekly curated reports of the best luxury handbag price drops tracked by BagDrop across Fashionphile, Rebag, The RealReal, and Vestiaire.',
  alternates: { canonical: '/intel/weekly-drops' },
  openGraph: {
    title: 'Weekly Luxury Bag Drop Reports | BagDrop',
    description: 'Browse weekly curated reports of the best luxury handbag price drops tracked by BagDrop.',
    url: '/intel/weekly-drops',
    type: 'website',
  },
}

async function getWeeks() {
  try {
    return await fetchApi('/api/intel/weekly-drops?weeks=12')
  } catch {
    return []
  }
}

export default async function WeeklyDropsIndexPage() {
  const weeks = await getWeeks()
  const weeksWithListings = weeks.filter((w) => w.listing_count > 0)

  return (
    <div className="min-h-screen bg-[#fffdf8]">
      <Header />

      <main className="mx-auto max-w-4xl px-4 py-6 sm:py-8">
        <div className="flex flex-wrap items-center gap-2 text-sm text-stone-500">
          <Link href="/" className="transition-colors hover:text-stone-900">Feed</Link>
          <span>/</span>
          <Link href="/intel" className="transition-colors hover:text-stone-900">Intel</Link>
          <span>/</span>
          <span className="text-stone-700">Weekly drops</span>
        </div>

        <div className="mt-8">
          <p className="mb-2 text-[11px] uppercase tracking-[0.25em] text-pink-500">Weekly Reports</p>
          <h1 className="text-3xl font-semibold text-stone-900 sm:text-4xl">Weekly drop archives</h1>
          <p className="mt-4 max-w-2xl text-base leading-7 text-stone-600">
            Each week BagDrop surfaces the strongest markdowns across Fashionphile, Rebag, The RealReal, and Vestiaire.
            Browse past reports to track market patterns over time.
          </p>
        </div>

        {weeksWithListings.length === 0 ? (
          <div className="mt-12 rounded-2xl border border-stone-200 bg-[#fffaf2] p-8 text-center">
            <p className="text-stone-500 text-sm">No weekly reports yet. Check back after the first scrape cycle.</p>
          </div>
        ) : (
          <div className="mt-8 divide-y divide-stone-100">
            {weeks.map((week) => (
              <Link
                key={week.week_start}
                href={`/intel/weekly-drops/${week.week_start}`}
                className="group flex items-center justify-between py-5 transition-colors hover:bg-[#fffaf2] -mx-4 px-4 rounded-xl"
              >
                <div>
                  <p className="font-semibold text-stone-900 group-hover:text-pink-600 transition-colors">
                    Week of {week.week_label}
                  </p>
                  <p className="mt-1 text-sm text-stone-500">
                    {week.listing_count > 0
                      ? `${week.listing_count} new listings${week.avg_drop_pct ? ` · avg −${week.avg_drop_pct}% off` : ''}`
                      : 'No listings this week'}
                  </p>
                </div>
                <span className="text-stone-400 group-hover:text-pink-500 transition-colors text-lg">→</span>
              </Link>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
