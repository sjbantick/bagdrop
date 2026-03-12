import Header from '@/components/Header'
import { fetchApi } from '@/lib/api'
import { formatCurrency, platformLabel } from '@/lib/format'
import { headers } from 'next/headers'
import Link from 'next/link'
import { notFound } from 'next/navigation'

export const metadata = {
  title: 'Ops',
  description: 'Internal scraper freshness and click activity dashboard for BagDrop.',
  robots: {
    index: false,
    follow: false,
  },
}

const OPS_DASHBOARD_TOKEN = process.env.OPS_DASHBOARD_TOKEN?.trim() || ''
const IS_DEVELOPMENT = process.env.NODE_ENV !== 'production'

async function getOpsSummary(excludeIp) {
  try {
    const params = new URLSearchParams()
    if (OPS_DASHBOARD_TOKEN) {
      params.set('token', OPS_DASHBOARD_TOKEN)
    }
    if (excludeIp) {
      params.set('exclude_ips', excludeIp)
    }
    const query = params.toString()
    return await fetchApi(`/api/admin/ops-summary${query ? `?${query}` : ''}`)
  } catch {
    return null
  }
}

async function getTopClicks(excludeIp) {
  try {
    const params = new URLSearchParams({ days: '7', limit: '6' })
    if (OPS_DASHBOARD_TOKEN) {
      params.set('token', OPS_DASHBOARD_TOKEN)
    }
    if (excludeIp) {
      params.set('exclude_ips', excludeIp)
    }
    return await fetchApi(`/api/admin/clicks/top?${params.toString()}`)
  } catch {
    return null
  }
}

function formatDateTime(value) {
  if (!value) {
    return 'Never'
  }

  return new Date(value).toLocaleString()
}

export default async function OpsPage({ searchParams }) {
  if ((OPS_DASHBOARD_TOKEN && searchParams?.token !== OPS_DASHBOARD_TOKEN) || (!OPS_DASHBOARD_TOKEN && !IS_DEVELOPMENT)) {
    notFound()
  }

  const headerStore = headers()
  const forwardedFor = headerStore.get('x-forwarded-for') || ''
  const currentIp = forwardedFor.split(',')[0]?.trim() || headerStore.get('x-real-ip') || ''
  const manualExcludeIp = searchParams?.exclude_ip?.trim?.() || ''
  const excludedIp = manualExcludeIp || currentIp

  const [summary, topClicks] = await Promise.all([getOpsSummary(excludedIp), getTopClicks(excludedIp)])
  const stalePlatforms = summary?.platforms.filter((platform) => platform.stale).length ?? 0

  return (
    <div className="min-h-screen bg-black">
      <Header />

      <main className="max-w-7xl mx-auto px-4 py-8">
        <section className="rounded-3xl border border-gray-800 bg-gradient-to-br from-gray-950 via-black to-gray-950 p-6 md:p-8">
          <p className="text-[11px] uppercase tracking-[0.3em] text-red-500 mb-3">Internal Ops</p>
          <div className="flex flex-col gap-8 xl:flex-row xl:items-end xl:justify-between">
            <div className="max-w-3xl">
              <h1 className="text-4xl md:text-5xl font-semibold text-white">Scraper health and monetization pulse</h1>
              <p className="mt-4 text-base md:text-lg leading-8 text-gray-300">
                This page replaces the old Paperclip board for day-to-day operating visibility. It shows scraper
                freshness, recent failures, live listing counts, and whether outbound click intent is actually flowing.
              </p>
              {excludedIp && (
                <p className="mt-3 text-sm text-gray-400">
                  Traffic metrics below exclude your IP: <span className="font-mono text-gray-200">{excludedIp}</span>
                </p>
              )}
            </div>

            <div className="grid grid-cols-2 lg:grid-cols-3 gap-4 xl:min-w-[620px]">
              <div className="rounded-2xl border border-gray-800 bg-black/60 p-4">
                <p className="text-gray-500 text-sm">Generated</p>
                <p className="mt-2 text-xl font-semibold text-white">
                  {summary ? formatDateTime(summary.generated_at) : 'Unavailable'}
                </p>
              </div>
              <div className="rounded-2xl border border-gray-800 bg-black/60 p-4">
                <p className="text-gray-500 text-sm">Stale after</p>
                <p className="mt-2 text-3xl font-semibold text-white">
                  {summary ? `${summary.stale_after_hours}h` : 'N/A'}
                </p>
              </div>
              <div className="rounded-2xl border border-gray-800 bg-black/60 p-4">
                <p className="text-gray-500 text-sm">Stale platforms</p>
                <p className={`mt-2 text-3xl font-semibold ${stalePlatforms ? 'text-red-400' : 'text-white'}`}>
                  {stalePlatforms}
                </p>
              </div>
              <div className="rounded-2xl border border-gray-800 bg-black/60 p-4">
                <p className="text-gray-500 text-sm">Clicks 24h</p>
                <p className="mt-2 text-3xl font-semibold text-white">
                  {summary?.total_outbound_clicks_24h ?? 0}
                </p>
              </div>
              <div className="rounded-2xl border border-gray-800 bg-black/60 p-4">
                <p className="text-gray-500 text-sm">Active watches</p>
                <p className="mt-2 text-3xl font-semibold text-white">
                  {summary?.active_watch_subscriptions ?? 0}
                </p>
              </div>
              <div className="rounded-2xl border border-gray-800 bg-black/60 p-4">
                <p className="text-gray-500 text-sm">Alert deliveries 24h</p>
                <p className="mt-2 text-3xl font-semibold text-white">
                  {summary?.watch_alert_deliveries_24h ?? 0}
                </p>
              </div>
            </div>
          </div>
        </section>

        {!summary ? (
          <section className="mt-8 rounded-2xl border border-red-900/40 bg-red-950/10 p-6 text-red-200">
            Ops summary is unavailable. Check API connectivity and database initialization.
          </section>
        ) : (
          <>
            <section className="mt-8 grid grid-cols-1 md:grid-cols-2 gap-5">
              {summary.platforms.map((platform) => (
                <article
                  key={platform.platform}
                  className="rounded-2xl border border-gray-800 bg-gray-950 p-5"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div>
                      <p className="text-[11px] uppercase tracking-[0.25em] text-red-500 mb-2">Platform</p>
                      <h2 className="text-2xl font-semibold text-white">{platformLabel(platform.platform)}</h2>
                    </div>
                    <div
                      className={`rounded-full px-3 py-1 text-xs font-mono border ${
                        platform.stale
                          ? 'border-red-500/40 bg-red-500/10 text-red-300'
                          : 'border-green-500/40 bg-green-500/10 text-green-300'
                      }`}
                    >
                      {platform.stale ? 'STALE' : 'FRESH'}
                    </div>
                  </div>

                  <div className="mt-5 grid grid-cols-2 gap-4 text-sm">
                    <div className="rounded-2xl border border-gray-800 bg-black/50 p-4">
                      <p className="text-gray-500">Last attempt</p>
                      <p className="mt-2 font-semibold text-white">{formatDateTime(platform.last_attempt_at)}</p>
                    </div>
                    <div className="rounded-2xl border border-gray-800 bg-black/50 p-4">
                      <p className="text-gray-500">Last success</p>
                      <p className="mt-2 font-semibold text-white">{formatDateTime(platform.last_success_at)}</p>
                    </div>
                    <div className="rounded-2xl border border-gray-800 bg-black/50 p-4">
                      <p className="text-gray-500">Active listings</p>
                      <p className="mt-2 font-semibold text-white">{platform.active_listings.toLocaleString()}</p>
                    </div>
                    <div className="rounded-2xl border border-gray-800 bg-black/50 p-4">
                      <p className="text-gray-500">Clicks 24h</p>
                      <p className="mt-2 font-semibold text-white">{platform.outbound_clicks_24h.toLocaleString()}</p>
                    </div>
                  </div>

                  <div className="mt-5 rounded-2xl border border-gray-800 bg-black/50 p-4 text-sm leading-7 text-gray-300">
                    <p>
                      Last listing sync: <span className="text-white">{formatDateTime(platform.last_listing_sync_at)}</span>
                    </p>
                    <p>
                      Last run status:{' '}
                      <span className={platform.last_run_success ? 'text-green-300' : 'text-red-300'}>
                        {platform.last_run_success == null ? 'Unknown' : platform.last_run_success ? 'Success' : 'Failed'}
                      </span>
                    </p>
                    <p>
                      Listings found on last run:{' '}
                      <span className="text-white">
                        {platform.listings_found == null ? 'N/A' : platform.listings_found.toLocaleString()}
                      </span>
                    </p>
                    {platform.error_message && (
                      <p>
                        Last error: <span className="text-red-300">{platform.error_message}</span>
                      </p>
                    )}
                  </div>
                </article>
              ))}
            </section>

            <section className="mt-8 grid grid-cols-1 xl:grid-cols-2 gap-5">
              <article className="rounded-2xl border border-gray-800 bg-gray-950 p-5">
                <p className="text-[11px] uppercase tracking-[0.25em] text-red-500 mb-2">Retention Ops</p>
                <h2 className="text-2xl font-semibold text-white">Alerting readiness</h2>
                <div className="mt-5 grid grid-cols-1 sm:grid-cols-2 gap-4 text-sm">
                  <div className="rounded-2xl border border-gray-800 bg-black/50 p-4">
                    <p className="text-gray-500">SMTP</p>
                    <p className={`mt-2 font-semibold ${summary.smtp_configured ? 'text-green-300' : 'text-red-300'}`}>
                      {summary.smtp_configured ? 'Configured' : 'Missing'}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-gray-800 bg-black/50 p-4">
                    <p className="text-gray-500">Watch alert scheduler</p>
                    <p className={`mt-2 font-semibold ${summary.watch_alert_scheduler_enabled ? 'text-green-300' : 'text-red-300'}`}>
                      {summary.watch_alert_scheduler_enabled ? 'Enabled' : 'Disabled'}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-gray-800 bg-black/50 p-4">
                    <p className="text-gray-500">Digest scheduler</p>
                    <p className={`mt-2 font-semibold ${summary.intelligence_digest_enabled ? 'text-green-300' : 'text-gray-300'}`}>
                      {summary.intelligence_digest_enabled ? 'Enabled' : 'Disabled'}
                    </p>
                  </div>
                  <div className="rounded-2xl border border-gray-800 bg-black/50 p-4">
                    <p className="text-gray-500">Digest recipients</p>
                    <p className="mt-2 font-semibold text-white">
                      {summary.intelligence_digest_recipient_count}
                    </p>
                  </div>
                </div>
              </article>

              <article className="rounded-2xl border border-gray-800 bg-gray-950 p-5">
                <p className="text-[11px] uppercase tracking-[0.25em] text-red-500 mb-2">Operating Interpretation</p>
                <h2 className="text-2xl font-semibold text-white">What this means</h2>
                <div className="mt-5 space-y-3 text-sm leading-7 text-gray-300">
                  <p>
                    Scrapers tell us whether supply is flowing in. Watch deliveries tell us whether BagDrop can turn
                    that supply into a retention loop.
                  </p>
                  <p>
                    SMTP and scheduler status should be green before we spend time on more list growth, otherwise new
                    watch signups will accumulate without any downstream value.
                  </p>
                  <p>
                    Digest recipients staying at zero is acceptable in setup mode, but not once the frontend/domain
                    cutover is complete and BagDrop starts acting like a daily intelligence product.
                  </p>
                </div>
              </article>
            </section>

            {topClicks && (
              <section className="mt-8 grid grid-cols-1 xl:grid-cols-2 gap-5">
                <article className="rounded-2xl border border-gray-800 bg-gray-950 p-5">
                  <p className="text-[11px] uppercase tracking-[0.25em] text-red-500 mb-2">Top Clicked Listings</p>
                  <h2 className="text-2xl font-semibold text-white">Outbound intent in the last {topClicks.days} days</h2>
                  <div className="mt-5 space-y-3">
                    {topClicks.listings.map((item) => (
                      <Link
                        key={item.listing_id}
                        href={item.detail_path}
                        className="flex items-center justify-between rounded-2xl border border-gray-800 bg-black/50 px-4 py-3 transition-colors hover:border-red-500"
                      >
                        <div>
                          <p className="text-white">{item.brand} {item.model}</p>
                          <p className="text-xs text-gray-500">{platformLabel(item.platform)} · {formatCurrency(item.current_price)}</p>
                        </div>
                        <span className="rounded-full border border-gray-700 px-3 py-1 text-xs font-mono text-white">
                          {item.click_count} clicks
                        </span>
                      </Link>
                    ))}
                  </div>
                </article>

                <article className="rounded-2xl border border-gray-800 bg-gray-950 p-5">
                  <p className="text-[11px] uppercase tracking-[0.25em] text-red-500 mb-2">Top Clicked Markets</p>
                  <h2 className="text-2xl font-semibold text-white">Where click intent is concentrating</h2>
                  <div className="mt-5 space-y-3">
                    {topClicks.markets.map((item) => (
                      <Link
                        key={item.canonical_path}
                        href={item.canonical_path}
                        className="flex items-center justify-between rounded-2xl border border-gray-800 bg-black/50 px-4 py-3 transition-colors hover:border-red-500"
                      >
                        <div>
                          <p className="text-white">{item.brand} {item.model}</p>
                          <p className="text-xs text-gray-500">{item.canonical_path}</p>
                        </div>
                        <span className="rounded-full border border-gray-700 px-3 py-1 text-xs font-mono text-white">
                          {item.click_count} clicks
                        </span>
                      </Link>
                    ))}
                  </div>
                </article>
              </section>
            )}

            {topClicks && (
              <section className="mt-5 grid grid-cols-1 xl:grid-cols-3 gap-5">
                <article className="rounded-2xl border border-gray-800 bg-gray-950 p-5">
                  <p className="text-[11px] uppercase tracking-[0.25em] text-red-500 mb-2">Top Platforms</p>
                  <h2 className="text-2xl font-semibold text-white">Which marketplaces monetize the demand</h2>
                  <div className="mt-5 space-y-3">
                    {topClicks.platforms.length ? topClicks.platforms.map((item) => (
                      <div
                        key={item.platform}
                        className="flex items-center justify-between rounded-2xl border border-gray-800 bg-black/50 px-4 py-3"
                      >
                        <div>
                          <p className="text-white">{platformLabel(item.platform)}</p>
                          <p className="text-xs text-gray-500">
                            {item.unique_listings} listings · {item.unique_markets} markets
                          </p>
                        </div>
                        <span className="rounded-full border border-gray-700 px-3 py-1 text-xs font-mono text-white">
                          {item.click_count} clicks
                        </span>
                      </div>
                    )) : (
                      <div className="rounded-2xl border border-dashed border-gray-800 bg-black/40 px-4 py-5 text-sm text-gray-500">
                        No marketplace click breakdown yet.
                      </div>
                    )}
                  </div>
                </article>

                <article className="rounded-2xl border border-gray-800 bg-gray-950 p-5">
                  <p className="text-[11px] uppercase tracking-[0.25em] text-red-500 mb-2">Top Surfaces</p>
                  <h2 className="text-2xl font-semibold text-white">Where BagDrop is producing click intent</h2>
                  <div className="mt-5 space-y-3">
                    {topClicks.surfaces.length ? topClicks.surfaces.map((item) => (
                      <div
                        key={item.surface}
                        className="flex items-center justify-between rounded-2xl border border-gray-800 bg-black/50 px-4 py-3"
                      >
                        <div>
                          <p className="text-white">{item.surface}</p>
                          <p className="text-xs text-gray-500">
                            {item.unique_listings} listings · {item.unique_markets} markets
                          </p>
                        </div>
                        <span className="rounded-full border border-gray-700 px-3 py-1 text-xs font-mono text-white">
                          {item.click_count} clicks
                        </span>
                      </div>
                    )) : (
                      <div className="rounded-2xl border border-dashed border-gray-800 bg-black/40 px-4 py-5 text-sm text-gray-500">
                        No outbound click surfaces recorded yet.
                      </div>
                    )}
                  </div>
                </article>

                <article className="rounded-2xl border border-gray-800 bg-gray-950 p-5">
                  <p className="text-[11px] uppercase tracking-[0.25em] text-red-500 mb-2">Top Contexts</p>
                  <h2 className="text-2xl font-semibold text-white">Which journeys convert curiosity into exits</h2>
                  <div className="mt-5 space-y-3">
                    {topClicks.contexts.length ? topClicks.contexts.map((item) => (
                      <div
                        key={item.context}
                        className="flex items-center justify-between rounded-2xl border border-gray-800 bg-black/50 px-4 py-3"
                      >
                        <div>
                          <p className="text-white">{item.context}</p>
                          <p className="text-xs text-gray-500">Downstream click context</p>
                        </div>
                        <span className="rounded-full border border-gray-700 px-3 py-1 text-xs font-mono text-white">
                          {item.click_count} clicks
                        </span>
                      </div>
                    )) : (
                      <div className="rounded-2xl border border-dashed border-gray-800 bg-black/40 px-4 py-5 text-sm text-gray-500">
                        No click contexts recorded yet.
                      </div>
                    )}
                  </div>
                </article>
              </section>
            )}
          </>
        )}
      </main>
    </div>
  )
}
