'use client'

import Link from 'next/link'
import { useEffect, useState } from 'react'
import ListingCard from '@/components/ListingCard'
import Header from '@/components/Header'
import Filters from '@/components/Filters'
import FeaturedMarkets from '@/components/FeaturedMarkets'
import ArbitrageRadar from '@/components/ArbitrageRadar'
import BagIndexBoard from '@/components/BagIndexBoard'
import NewDropsRadar from '@/components/NewDropsRadar'
import HomeWatchSignup from '@/components/HomeWatchSignup'
import { getApiUrl } from '@/lib/api'

export default function HomePageClient({
  initialListings = [],
  initialFeaturedMarkets = [],
  initialArbitrageOpportunities = [],
  initialBagIndex = [],
  initialNewDrops = [],
  initialStats = null,
}) {
  const [listings, setListings] = useState(initialListings)
  const [featuredMarkets, setFeaturedMarkets] = useState(initialFeaturedMarkets)
  const [arbitrageOpportunities, setArbitrageOpportunities] = useState(initialArbitrageOpportunities)
  const [bagIndex, setBagIndex] = useState(initialBagIndex)
  const [newDrops, setNewDrops] = useState(initialNewDrops)
  const [stats, setStats] = useState(initialStats)
  const [loading, setLoading] = useState(false)
  const [loadingMore, setLoadingMore] = useState(false)
  const [nextCursor, setNextCursor] = useState(null)
  const [hasMore, setHasMore] = useState(false)
  const [filters, setFilters] = useState({
    brand: '',
    model: '',
    sortBy: 'drop_pct',
    minDropPct: 0,
    platform: '',
  })

  const buildParams = (cursor = null) => {
    const params = new URLSearchParams({
      limit: 60,
      sort_by: filters.sortBy,
      min_drop_pct: filters.minDropPct,
    })
    if (filters.brand) params.append('brand', filters.brand)
    if (filters.model) params.append('model', filters.model)
    if (filters.platform) params.append('platform', filters.platform)
    if (cursor) params.append('cursor', cursor)
    return params
  }

  const fetchListings = async () => {
    setLoading(true)
    try {
      const response = await fetch(getApiUrl(`/api/listings?${buildParams()}`))
      const data = await response.json()
      setListings(data.items ?? data)
      setNextCursor(data.next_cursor ?? null)
      setHasMore(data.has_more ?? false)
    } catch (error) {
      console.error('Failed to fetch listings:', error)
    } finally {
      setLoading(false)
    }
  }

  const loadMore = async () => {
    if (!nextCursor || loadingMore) return
    setLoadingMore(true)
    try {
      const response = await fetch(getApiUrl(`/api/listings?${buildParams(nextCursor)}`))
      const data = await response.json()
      setListings((prev) => [...prev, ...(data.items ?? [])])
      setNextCursor(data.next_cursor ?? null)
      setHasMore(data.has_more ?? false)
    } catch (error) {
      console.error('Failed to load more listings:', error)
    } finally {
      setLoadingMore(false)
    }
  }

  const refreshStats = async () => {
    try {
      const response = await fetch(getApiUrl('/api/stats'))
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    }
  }

  useEffect(() => {
    setFeaturedMarkets(initialFeaturedMarkets)
    setArbitrageOpportunities(initialArbitrageOpportunities)
    setBagIndex(initialBagIndex)
    setNewDrops(initialNewDrops)
  }, [initialArbitrageOpportunities, initialBagIndex, initialFeaturedMarkets, initialNewDrops])

  useEffect(() => {
    const hasActiveFilters = Boolean(filters.brand || filters.model || filters.platform || filters.minDropPct || filters.sortBy !== 'drop_pct')
    if (!hasActiveFilters) {
      setListings(initialListings)
      setNextCursor(null)
      setHasMore(false)
      setLoading(false)
      return
    }

    fetchListings()
  }, [filters, initialListings])

  useEffect(() => {
    const interval = setInterval(refreshStats, 60000)
    return () => clearInterval(interval)
  }, [])

  return (
    <div className="min-h-screen bg-[#fffdf8]">
      <Header stats={stats} />

      {stats && (
        <div className="border-b border-stone-200 bg-[#f8f2ea]">
          <div className="mx-auto flex max-w-7xl flex-wrap gap-x-6 gap-y-1 px-4 py-2 text-[11px] font-mono text-stone-600 sm:text-xs">
            <span>
              <span className="text-stone-900">{stats.total_active_listings?.toLocaleString()}</span> active drops
            </span>
            {stats.drops_today > 0 && (
              <span>
                <span className="text-pink-600 font-semibold">{stats.drops_today.toLocaleString()}</span> dropped today
              </span>
            )}
            {stats.avg_drop_pct && (
              <span>
                avg drop: <span className="text-pink-600">-{stats.avg_drop_pct}%</span>
              </span>
            )}
            {stats.biggest_drop_pct && (
              <span>
                biggest drop: <span className="font-bold text-pink-700">-{stats.biggest_drop_pct}%</span>
              </span>
            )}
          </div>
        </div>
      )}

      <div className="mx-auto max-w-7xl px-4 py-6 sm:py-8">
        <section className="mb-8 rounded-3xl border border-stone-200 bg-[#f7f1e8] p-5 shadow-[0_12px_40px_rgba(206,182,150,0.10)] sm:p-7">
          <div className="grid gap-6 lg:grid-cols-[1.2fr_0.8fr] lg:items-end">
            <div>
              <p className="mb-3 text-[11px] uppercase tracking-[0.3em] text-pink-500">BagDrop</p>
              <h1 className="max-w-4xl text-3xl font-semibold text-stone-950 sm:text-4xl md:text-5xl">
                Track live luxury bag markdowns before they disappear.
              </h1>
              <p className="mt-4 max-w-3xl text-sm leading-7 text-stone-600 sm:text-base sm:leading-8">
                BagDrop scans live resale inventory, surfaces meaningful drops, and keeps the market context on-site so
                you can judge whether a listing is genuinely attractive before clicking out.
              </p>
              <div className="mt-6 flex flex-col gap-3 sm:flex-row">
                <a
                  href="#feed"
                  className="inline-flex items-center justify-center rounded-full bg-pink-500 px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-pink-400"
                >
                  Browse live drops
                </a>
                <Link
                  href="/intel"
                  className="inline-flex items-center justify-center rounded-full border border-stone-300 bg-white px-5 py-3 text-sm font-medium text-stone-700 transition-colors hover:border-pink-300 hover:text-pink-600"
                >
                  Read intel brief
                </Link>
              </div>
            </div>

            <div className="grid grid-cols-1 gap-3 sm:grid-cols-3 lg:grid-cols-1">
              <div className="rounded-2xl border border-stone-200 bg-white/80 p-4">
                <p className="text-[11px] uppercase tracking-[0.2em] text-stone-500">Trust</p>
                <p className="mt-2 text-sm leading-6 text-stone-700">
                  Freshness labels and sold-listing quarantine keep dead inventory out of the feed.
                </p>
              </div>
              <div className="rounded-2xl border border-stone-200 bg-white/80 p-4">
                <p className="text-[11px] uppercase tracking-[0.2em] text-stone-500">Signal</p>
                <p className="mt-2 text-sm leading-6 text-stone-700">
                  Arbitrage, BagIndex, and new-drop ranking push the strongest opportunities to the top.
                </p>
              </div>
              <div className="rounded-2xl border border-stone-200 bg-white/80 p-4">
                <p className="text-[11px] uppercase tracking-[0.2em] text-stone-500">Coverage</p>
                <p className="mt-2 text-sm leading-6 text-stone-700">
                  Live launch sources now include Fashionphile, Rebag, Yoogi, Cosette, and The Purse Affair.
                </p>
              </div>
            </div>
          </div>
        </section>

        <HomeWatchSignup markets={featuredMarkets} />
        <FeaturedMarkets markets={featuredMarkets} />
        <ArbitrageRadar opportunities={arbitrageOpportunities} />
        <BagIndexBoard snapshots={bagIndex} />
        <NewDropsRadar opportunities={newDrops} />

        <Filters filters={filters} setFilters={setFilters} />

        {loading ? (
          <div className="text-center py-16">
            <p className="text-sm font-mono animate-pulse text-stone-500">scanning platforms...</p>
          </div>
        ) : listings.length === 0 ? (
          <div className="text-center py-16">
            <p className="mb-2 text-2xl text-stone-500">No drops found</p>
            <p className="text-sm text-stone-500">Scrapers are running. Check back soon.</p>
          </div>
        ) : (
          <>
            <div id="feed" className="mb-4 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
              <div>
                <p className="text-[11px] uppercase tracking-[0.25em] text-pink-500">Live Feed</p>
                <p className="mt-1 text-sm text-stone-500">
                  {listings.length} listings ranked by markdown, freshness, and market relevance.
                </p>
              </div>
            </div>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 sm:gap-5 lg:grid-cols-3 xl:grid-cols-4">
              {listings.map((listing) => (
                <ListingCard key={listing.id} listing={listing} />
              ))}
            </div>

            {hasMore && (
              <div className="mt-10 flex justify-center">
                <button
                  onClick={loadMore}
                  disabled={loadingMore}
                  className="rounded-full border border-stone-300 bg-white px-8 py-3 text-sm font-medium text-stone-700 transition-colors hover:border-pink-300 hover:text-pink-600 disabled:opacity-50"
                >
                  {loadingMore ? 'Loading...' : 'Load more drops'}
                </button>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
