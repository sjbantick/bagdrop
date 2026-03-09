'use client'

const PLATFORMS = [
  { value: '', label: 'All Platforms' },
  { value: 'fashionphile', label: 'Fashionphile' },
  { value: 'rebag', label: 'Rebag' },
  { value: 'realreal', label: 'The RealReal' },
  { value: 'vestiaire', label: 'Vestiaire' },
]

export default function Filters({ filters, setFilters }) {
  return (
    <div className="mb-6">
      {/* Platform tabs */}
      <div className="flex gap-2 mb-4 overflow-x-auto pb-1">
        {PLATFORMS.map((p) => (
          <button
            key={p.value}
            onClick={() => setFilters({ ...filters, platform: p.value })}
            className={`px-4 py-1.5 rounded-full text-xs font-mono whitespace-nowrap transition-colors ${
              filters.platform === p.value
                ? 'bg-red-600 text-white'
                : 'bg-gray-900 border border-gray-800 text-gray-400 hover:border-gray-600'
            }`}
          >
            {p.label}
          </button>
        ))}
      </div>

      {/* Filter row */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        <input
          type="text"
          placeholder="Brand (e.g. Hermès)"
          value={filters.brand}
          onChange={(e) => setFilters({ ...filters, brand: e.target.value })}
          className="bg-gray-900 border border-gray-800 rounded px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-red-500"
        />

        <input
          type="text"
          placeholder="Model (e.g. Birkin)"
          value={filters.model}
          onChange={(e) => setFilters({ ...filters, model: e.target.value })}
          className="bg-gray-900 border border-gray-800 rounded px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-red-500"
        />

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
    </div>
  )
}
