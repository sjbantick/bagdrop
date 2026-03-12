import { formatCurrency, formatPercent } from '@/lib/format'

export default function BagIndexBoard({ snapshots = [] }) {
  if (!snapshots.length) {
    return null
  }

  return (
    <section className="mb-8">
      <div className="flex items-end justify-between gap-4 mb-4">
        <div>
          <p className="text-[11px] uppercase tracking-[0.25em] text-red-500 mb-2">BagIndex</p>
          <h2 className="text-2xl font-semibold text-white">Brand-level price health</h2>
        </div>
        <p className="text-sm text-gray-500 max-w-md text-right hidden md:block">
          BagIndex measures the current average resale price of a brand against its observed peak average inside
          BagDrop. Lower numbers mean more price pressure.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">
        {snapshots.map((snapshot) => {
          const tone =
            snapshot.index_value <= 80 ? 'text-red-400' :
            snapshot.index_value <= 92 ? 'text-orange-300' :
            'text-green-300'
          const trendLabel =
            snapshot.trend === 'up' ? 'improving' :
            snapshot.trend === 'down' ? 'under pressure' :
            snapshot.trend === 'flat' ? 'flat' :
            'new'
          const trendTone =
            snapshot.trend === 'up' ? 'text-green-300' :
            snapshot.trend === 'down' ? 'text-red-300' :
            'text-gray-400'

          return (
            <div
              key={snapshot.brand}
              className="rounded-2xl border border-gray-800 bg-gradient-to-br from-gray-950 via-gray-900 to-black p-5"
            >
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="text-sm font-medium text-gray-400">Brand</p>
                  <h3 className="mt-1 text-xl font-semibold text-white">{snapshot.brand}</h3>
                  <p className={`mt-2 text-xs font-mono ${trendTone}`}>
                    {snapshot.delta_pct != null ? `${snapshot.delta_pct > 0 ? '+' : ''}${snapshot.delta_pct} vs last` : trendLabel}
                  </p>
                </div>
                <div className={`text-right ${tone}`}>
                  <p className="text-3xl font-semibold">{snapshot.index_value}</p>
                  <p className="text-xs font-mono">index</p>
                </div>
              </div>

              <div className="mt-6 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <p className="text-gray-500">Current avg</p>
                  <p className="mt-1 font-semibold text-white">{formatCurrency(snapshot.current_avg_price)}</p>
                </div>
                <div>
                  <p className="text-gray-500">Peak avg</p>
                  <p className="mt-1 font-semibold text-white">{formatCurrency(snapshot.peak_avg_price)}</p>
                </div>
                <div>
                  <p className="text-gray-500">Active listings</p>
                  <p className="mt-1 font-semibold text-white">{snapshot.active_listings_count}</p>
                </div>
                <div>
                  <p className="text-gray-500">Avg drop</p>
                  <p className="mt-1 font-semibold text-red-300">
                    {snapshot.avg_drop_pct ? `-${formatPercent(snapshot.avg_drop_pct)}` : 'N/A'}
                  </p>
                </div>
              </div>
            </div>
          )
        })}
      </div>
    </section>
  )
}
