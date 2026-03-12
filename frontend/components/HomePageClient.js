'use client'

import { useEffect, useState } from 'react'
import ListingCard from '@/components/ListingCard'
import Header from '@/components/Header'
import Filters from '@/components/Filters'
import FeaturedMarkets from '@/components/FeaturedMarkets'
import ArbitrageRadar from '@/components/ArbitrageRadar'
import BagIndexBoard from '@/components/BagIndexBoard'
import NewDropsRadar from '@/components/NewDropsRadar'
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
  const [filters, setFilters] = useState({
    brand: '',
    model: '',
    sortBy: 'drop_pct',
    minDropPct: 0,
    platform: '',
  })

  const fetchListings = async () => {
    setLoading(true)
    try {
      const params = new URLSearchParams({
        limit: 60,
        offset: 0,
        sort_by: filters.sortBy,
        min_drop_pct: filters.minDropPct,
      })
      if (filters.brand) params.append('brand', filters.brand)
      if (filters.model) params.append('model', filters.model)
      if (filters.platform) params.append('platform', filters.platform)

      const response = await fetch(getApiUrl(`/api/listings?${params}`))
      const data = await response.json()
      setListings(data)
    } catch (error) {
      console.error('Failed to fetch listings:', error)
    } finally {
      setLoading(false)
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
          <div className="mx-auto flex max-w-7xl gap-8 px-4 py-2 text-xs font-mono text-stone-600">
            <span>
              <span className="text-stone-900">{stats.total_active_listings?.toLocaleString()}</span> active drops
            </span>
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

      <div className="max-w-7xl mx-auto px-4 py-8">
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
            <p className="mb-4 text-sm font-mono text-stone-500">{listings.length} listings</p>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-5">
              {listings.map((listing) => (
                <ListingCard key={listing.id} listing={listing} />
              ))}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
