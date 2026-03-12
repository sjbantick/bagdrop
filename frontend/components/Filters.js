'use client'

import { useEffect, useMemo, useState } from 'react'
import { fetchApi } from '@/lib/api'

const PLATFORMS = [
  { value: '', label: 'All Platforms' },
  { value: 'fashionphile', label: 'Fashionphile' },
  { value: 'rebag', label: 'Rebag' },
  { value: 'realreal', label: 'The RealReal' },
  { value: 'vestiaire', label: 'Vestiaire' },
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

  return (
    <div className="mb-6">
      <div className="flex gap-2 mb-4 overflow-x-auto pb-1">
        {PLATFORMS.map((platform) => (
          <button
            key={platform.value}
            onClick={() => setFilters({ ...filters, platform: platform.value })}
            className={`px-4 py-1.5 rounded-full text-xs font-mono whitespace-nowrap transition-colors ${
              filters.platform === platform.value
                ? 'bg-red-600 text-white'
                : 'bg-gray-900 border border-gray-800 text-gray-400 hover:border-gray-600'
            }`}
          >
            {platform.label}
          </button>
        ))}
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <div>
          <input
            type="text"
            placeholder="Brand (e.g. Hermès)"
            value={filters.brand}
            onChange={(e) => setFilters({ ...filters, brand: e.target.value })}
            list="brand-suggestions"
            className="w-full bg-gray-900 border border-gray-800 rounded px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-red-500"
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
            className="w-full bg-gray-900 border border-gray-800 rounded px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-red-500"
          />
          <datalist id="model-suggestions">
            {models.map((model) => (
              <option key={model} value={model} />
            ))}
          </datalist>
        </div>

        <select
          value={filters.sortBy}
          onChange={(e) => setFilters({ ...filters, sortBy: e.target.value })}
          className="bg-gray-900 border border-gray-800 rounded px-3 py-2 text-sm text-white focus:outline-none focus:border-red-500"
        >
          <option value="drop_pct">Biggest % Drop</option>
          <option value="drop_amount">Biggest $ Drop</option>
          <option value="current_price">Price: High → Low</option>
          <option value="last_seen">Most Recent</option>
        </select>

        <div className="relative">
          <input
            type="number"
            placeholder="Min drop %"
            value={filters.minDropPct || ''}
            onChange={(e) => setFilters({ ...filters, minDropPct: parseFloat(e.target.value) || 0 })}
            className="w-full bg-gray-900 border border-gray-800 rounded px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-red-500"
            min="0"
            max="100"
          />
        </div>
      </div>

      <div className="mt-2 text-[11px] text-gray-600 font-mono">
        {matchedBrand
          ? `Model suggestions loaded for ${matchedBrand}`
          : 'Select an exact brand to unlock model suggestions'}
      </div>
    </div>
  )
}
