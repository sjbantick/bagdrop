'use client'

export default function Filters({ filters, setFilters }) {
  return (
    <div className="mb-8 bg-gray-900 rounded-lg p-6 border border-gray-800">
      <h2 className="text-lg font-semibold mb-4">Filters</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <input
          type="text"
          placeholder="Brand (e.g., Hermès)"
          value={filters.brand}
          onChange={(e) => setFilters({ ...filters, brand: e.target.value })}
          className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-red-500"
        />

        <input
          type="text"
          placeholder="Model (e.g., Birkin)"
          value={filters.model}
          onChange={(e) => setFilters({ ...filters, model: e.target.value })}
          className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-red-500"
        />

        <select
          value={filters.sortBy}
          onChange={(e) => setFilters({ ...filters, sortBy: e.target.value })}
          className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white focus:outline-none focus:border-red-500"
        >
          <option value="drop_pct">Biggest % Drop</option>
          <option value="drop_amount">Biggest $ Drop</option>
          <option value="current_price">Price (High to Low)</option>
          <option value="last_seen">Most Recent</option>
        </select>

        <input
          type="number"
          placeholder="Min drop %"
          value={filters.minDropPct}
          onChange={(e) => setFilters({ ...filters, minDropPct: parseFloat(e.target.value) || 0 })}
          className="bg-gray-800 border border-gray-700 rounded px-3 py-2 text-white placeholder-gray-500 focus:outline-none focus:border-red-500"
          min="0"
          max="100"
        />
      </div>
    </div>
  )
}
