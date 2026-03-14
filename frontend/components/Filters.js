'use client'

import { useEffect, useMemo, useState } from 'react'
import { fetchApi } from '@/lib/api'

const PLATFORMS = [
  { value: '', label: 'All Platforms' },
  { value: 'fashionphile', label: 'Fashionphile' },
  { value: 'rebag', label: 'Rebag' },
  { value: 'realreal', label: 'The RealReal' },
  { value: 'vestiaire', label: 'Vestiaire' },
  { value: 'yoogi', label: "Yoogi's Closet" },
  { value: 'cosette', label: 'Cosette' },
  { value: 'thepurseaffair', label: 'The Purse Affair' },
]

export default function Filters({ filters, setFilters }) {
  const [brands, setBrands] = useState([])
  const [models, setModels] = useState([])

  useEffect(() => {
    let cancelled = false

    async function loadBrands() {
      try {
        const data = await fetchApi('/api/brands')
        if (!cancelled) {
          setBrands(data)
        }
      } catch (error) {
        console.error('Failed to load brands:', error)
      }
    }

    loadBrands()

    return () => {
      cancelled = true
    }
  }, [])

  const matchedBrand = useMemo(() => {
    const input = filters.brand.trim().toLowerCase()
    if (!input) {
      return null
    }

    return brands.find((brand) => brand.toLowerCase() === input) || null
  }, [brands, filters.brand])

  useEffect(() => {
    let cancelled = false

    async function loadModels() {
      if (!matchedBrand) {
        setModels([])
        return
      }

      try {
        const encodedBrand = encodeURIComponent(matchedBrand)
        const data = await fetchApi(`/api/brands/${encodedBrand}/models`)
        if (!cancelled) {
          setModels(data)
        }
      } catch (error) {
        console.error('Failed to load models:', error)
      }
    }

    loadModels()

    return () => {
      cancelled = true
    }
  }, [matchedBrand])

  const DROP_THRESHOLDS = [
    { label: 'Any drop', value: 0 },
    { label: '10%+', value: 10 },
    { label: '20%+', value: 20 },
    { label: '30%+', value: 30 },
    { label: '50%+', value: 50 },
  ]

  const hasActiveFilters = Boolean(
    filters.brand || filters.model || filters.platform || filters.minDropPct || filters.sortBy !== 'drop_pct'
  )

  const clearFilters = () =>
    setFilters({ brand: '', model: '', sortBy: 'drop_pct', minDropPct: 0, platform: '' })

  return (
    <div className="mb-6 space-y-3">
      {/* Platform pills */}
      <div className="flex flex-wrap gap-2">
        {PLATFORMS.map((platform) => (
          <button
            key={platform.value}
            onClick={() => setFilters({ ...filters, platform: platform.value })}
            className={`px-4 py-1.5 rounded-full text-xs font-mono whitespace-nowrap transition-colors ${
              filters.platform === platform.value
                ? 'bg-pink-500 text-white'
                : 'border border-stone-300 bg-white text-stone-600 hover:border-pink-300'
            }`}
          >
            {platform.label}
          </button>
        ))}
      </div>

      {/* Drop % quick-select */}
      <div className="flex flex-wrap gap-2 items-center">
        <span className="text-[11px] font-mono text-stone-400 uppercase tracking-[0.15em]">Min drop</span>
        {DROP_THRESHOLDS.map((t) => (
          <button
            key={t.value}
            onClick={() => setFilters({ ...filters, minDropPct: t.value })}
            className={`px-3 py-1 rounded-full text-xs font-mono whitespace-nowrap transition-colors ${
              filters.minDropPct === t.value
                ? 'bg-stone-900 text-white'
                : 'border border-stone-300 bg-white text-stone-600 hover:border-stone-400'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {/* Brand / model / sort row */}
      <div className="grid grid-cols-1 gap-3 sm:grid-cols-3">
        <div>
          <input
            type="text"
            placeholder="Brand (e.g. Hermès)"
            value={filters.brand}
            onChange={(e) => setFilters({ ...filters, brand: e.target.value })}
            list="brand-suggestions"
            className="w-full rounded-xl border border-stone-300 bg-white px-3 py-2 text-sm text-stone-900 placeholder-stone-400 focus:border-pink-400 focus:outline-none"
          />
          <datalist id="brand-suggestions">
            {brands.map((brand) => (
              <option key={brand} value={brand} />
            ))}
          </datalist>
        </div>

        <div>
          <input
            type="text"
            placeholder="Model (e.g. Birkin)"
            value={filters.model}
            onChange={(e) => setFilters({ ...filters, model: e.target.value })}
            list="model-suggestions"
            className="w-full rounded-xl border border-stone-300 bg-white px-3 py-2 text-sm text-stone-900 placeholder-stone-400 focus:border-pink-400 focus:outline-none"
          />
          <datalist id="model-suggestions">
            {models.map((model) => (
              <option key={model} value={model} />
            ))}
          </datalist>
        </div>

        <div className="flex gap-2">
          <select
            value={filters.sortBy}
            onChange={(e) => setFilters({ ...filters, sortBy: e.target.value })}
            className="flex-1 rounded-xl border border-stone-300 bg-white px-3 py-2 text-sm text-stone-900 focus:border-pink-400 focus:outline-none"
          >
            <option value="drop_pct">Biggest % Drop</option>
            <option value="drop_amount">Biggest $ Drop</option>
            <option value="current_price">Price: High → Low</option>
            <option value="last_seen">Most Recent</option>
          </select>
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="rounded-xl border border-stone-300 bg-white px-3 py-2 text-xs text-stone-500 hover:border-pink-300 hover:text-pink-600 transition-colors whitespace-nowrap"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {matchedBrand && (
        <p className="text-[11px] font-mono text-stone-400">
          Showing model suggestions for {matchedBrand}
        </p>
      )}
    </div>
  )
}
