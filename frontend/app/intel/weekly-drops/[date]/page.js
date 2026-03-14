import Link from 'next/link'
import { notFound } from 'next/navigation'
import Header from '@/components/Header'
import ListingCard from '@/components/ListingCard'
import StructuredData from '@/components/StructuredData'
import { fetchApi } from '@/lib/api'
import { formatCurrency, formatPercent } from '@/lib/format'
import { absoluteUrl } from '@/lib/site'

async function getWeeklyDrops(date) {
  try {
    return await fetchApi(`/api/intel/weekly-drops/${date}?limit=20`)
  } catch {
    return null
  }
}

export async function generateStaticParams() {
  // Pre-render last 12 weeks
  const params = []
  const today = new Date()
  // Find Monday of current week
  const dayOfWeek = today.getDay() // 0=Sun
  const daysToMonday = dayOfWeek === 0 ? 6 : dayOfWeek - 1
  const monday = new Date(today)
  monday.setDate(today.getDate() - daysToMonday)

  for (let i = 0; i < 12; i++) {
    const d = new Date(monday)
    d.setDate(monday.getDate() - i * 7)
    params.push({ date: d.toISOString().slice(0, 10) })
  }
  return params
}

export async function generateMetadata({ params }) {
  const data = await getWeeklyDrops(params.date)
  if (!data) return { title: 'Weekly Drops | BagDrop' }

  const title = `Best Luxury Bag Drops: ${data.week_label} | BagDrop`
  const description = data.listing_count > 0
    ? `${data.listing_count} price-tracked luxury handbag listings for ${data.week_label}.${data.avg_drop_pct ? ` Average markdown: −${data.avg_drop_pct}%.` : ''} Top brands: ${data.top_brands.slice(0, 3).map((b) => b.brand).join(', ')}.`
    : `Weekly luxury handbag drop report for ${data.week_label} on BagDrop.`
  const pagePath = `/intel/weekly-drops/${params.date}`

  return {
    title,
    description,
    alternates: { canonical: pagePath },
    openGraph: {
      title,
      description,
      url: pagePath,
      type: 'article',
    },
    twitter: {
      card: 'summary_large_image',
      title,
      description,
    },
  }
}

export default async function WeeklyDropsPage({ params }) {
  const data = await getWeeklyDrops(params.date)
  if (!data) notFound()

  const hasListings = data.listings.length > 0

  return (
    <div className="min-h-screen bg-[#fffdf8]">
      <StructuredData
        data={{
          '@context': 'https://schema.org',
          '@type': 'ItemList',
          name: `Best Luxury Bag Drops: ${data.week_label}`,
          description: `Top price-tracked luxury handbag listings for ${data.week_label}, curated by BagDrop.`,
          url: absoluteUrl(`/intel/weekly-drops/${params.date}`),
          numberOfItems: data.listing_count,
          itemListElement: data.listings.map((l, i) => ({
            '@type': 'ListItem',
            position: i + 1,
            name: `${l.brand} ${l.model}`,
            url: absoluteUrl(`/listings/${l.id}`),
          })),
        }}
      />
      <Header />

      <main className="mx-auto max-w-7xl px-4 py-6 sm:py-8">
        {/* Breadcrumb */}
        <div className="flex flex-wrap items-center gap-2 text-sm text-stone-500">
          <Link href="/" className="transition-colors hover:text-stone-900">Feed</Link>
          <span>/</span>
          <Link href="/intel" className="transition-colors hover:text-stone-900">Intel</Link>
          <span>/</span>
          <Link href="/intel/weekly-drops" className="transition-colors hover:text-stone-900">Weekly drops</Link>
          <span>/</span>
          <span className="text-stone-700">{data.week_label}</span>
        </div>

        {/* Hero */}
        <section className="mt-8 rounded-3xl border border-stone-200 bg-[#f4eee6] p-6 md:p-10">
          <p className="mb-3 text-[11px] uppercase tracking-[0.3em] text-pink-500">Weekly Report</p>
          <h1 className="text-3xl font-semibold text-stone-950 sm:text-4xl md:text-5xl">
            Best drops: {data.week_label}
          </h1>

          {hasListings ? (
            <div className="mt-6 flex flex-wrap gap-6">
              <div>
                <p className="text-xs text-stone-500 uppercase tracking-widest">New listings</p>
                <p className="mt-1 text-2xl font-semibold text-stone-900">{data.listing_count}</p>
              </div>
              {data.avg_drop_pct && (
                <div>
                  <p className="text-xs text-stone-500 uppercase tracking-widest">Avg markdown</p>
                  <p className="mt-1 text-2xl font-semibold text-pink-600">−{data.avg_drop_pct}%</p>
                </div>
              )}
              {data.top_brands.length > 0 && (
                <div>
                  <p className="text-xs text-stone-500 uppercase tracking-widest">Top brands</p>
                  <p className="mt-1 text-base font-semibold text-stone-900">
                    {data.top_brands.slice(0, 3).map((b) => b.brand).join(' · ')}
                  </p>
                </div>
              )}
            </div>
          ) : (
            <p className="mt-4 text-stone-500">No new listings were tracked this week.</p>
          )}
        </section>

        {/* Brand breakdown */}
        {data.top_brands.length > 1 && (
          <section className="mt-8">
            <p className="mb-3 text-[11px] uppercase tracking-[0.25em] text-pink-500">By Brand</p>
            <div className="flex flex-wrap gap-3">
              {data.top_brands.map((b) => (
                <div
                  key={b.brand}
                  className="rounded-2xl border border-stone-200 bg-white px-4 py-3 text-sm"
                >
                  <p className="font-semibold text-stone-900">{b.brand}</p>
                  <p className="mt-0.5 text-stone-500">
                    {b.listing_count} listing{b.listing_count !== 1 ? 's' : ''}
                    {b.avg_drop_pct ? ` · avg −${b.avg_drop_pct}%` : ''}
                  </p>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* Listings grid */}
        {hasListings ? (
          <section className="mt-8">
            <p className="mb-3 text-[11px] uppercase tracking-[0.25em] text-pink-500">Top Drops This Week</p>
            <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-3">
              {data.listings.map((listing) => (
                <ListingCard key={listing.id} listing={listing} />
              ))}
            </div>
          </section>
        ) : (
          <div className="mt-12 rounded-2xl border border-stone-100 bg-[#fffaf2] p-8 text-center">
            <p className="text-stone-500 text-sm">No listings were tracked during this week.</p>
            <Link href="/intel/weekly-drops" className="mt-4 inline-block text-sm text-pink-500 hover:underline">
              View other weeks
            </Link>
          </div>
        )}

        {/* Nav between weeks */}
        <div className="mt-12 flex items-center justify-between border-t border-stone-200 pt-6 text-sm">
          <Link
            href={`/intel/weekly-drops/${new Date(new Date(params.date).getTime() - 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)}`}
            className="text-stone-500 transition-colors hover:text-stone-900"
          >
            ← Previous week
          </Link>
          <Link href="/intel/weekly-drops" className="text-stone-500 transition-colors hover:text-stone-900">
            All reports
          </Link>
          <Link
            href={`/intel/weekly-drops/${new Date(new Date(params.date).getTime() + 7 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10)}`}
            className="text-stone-500 transition-colors hover:text-stone-900"
          >
            Next week →
          </Link>
        </div>
      </main>
    </div>
  )
}
