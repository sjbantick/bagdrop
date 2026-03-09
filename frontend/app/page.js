'use client'

import { useState, useEffect } from 'react'
import ListingCard from '@/components/ListingCard'
import Header from '@/components/Header'
import Filters from '@/components/Filters'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function Home() {
  const [listings, setListings] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)
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

      const response = await fetch(`${API_URL}/api/listings?${params}`)
      const data = await response.json()
      setListings(data)
    } catch (error) {
      console.error('Failed to fetch listings:', error)
    } finally {
      setLoading(false)
    }
  }

  const fetchStats = async () => {
    try {
      const response = await fetch(`${API_URL}/api/stats`)
      const data = await response.json()
      setStats(data)
    } catch (error) {
      console.error('Failed to fetch stats:', error)
    }
  }

  useEffect(() => {
    fetchStats()
    const interval = setInterval(fetchStats, 60000) // refresh stats every minute
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    fetchListings()
  }, [filters])

  return (
    <div className="min-h-screen bg-black">
      <Header stats={stats} />

      {/* Stats ticker */}
      {stats && (
        <div className="border-b border-gray-800 bg-gray-950">
          <div className="max-w-7xl mx-auto px-4 py-2 flex gap-8 text-xs font-mono text-gray-400">
            <span>
              <span className="text-white">{stats.total_active_listings?.toLocaleString()}</span> active drops
            </span>
            {stats.avg_drop_pct && (
              <span>
                avg drop: <span className="text-red-400">−{stats.avg_drop_pct}%</span>
              </span>
            )}
            {stats.biggest_drop_pct && (
              <span>
                biggest drop: <span className="text-red-500 font-bold">−{stats.biggest_drop_pct}%</span>
              </span>
            )}
          </div>
        </div>
      )}

      <div className="max-w-7xl mx-auto px-4 py-8">
        <Filters filters={filters} setFilters={setFilters} />

        {loading ? (
          <div className="text-center py-16">
            <p className="text-gray-500 font-mono text-sm animate-pulse">scanning platforms...</p>
          </div>
        ) : listings.length === 0 ? (
          <div className="text-center py-16">
            <p className="text-gray-500 text-2xl mb-2">No drops found</p>
            <p className="text-gray-600 text-sm">Scrapers are running. Check back soon.</p>
          </div>
        ) : (
          <>
            <p className="text-gray-600 text-sm mb-4 font-mono">{listings.length} listings</p>
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
