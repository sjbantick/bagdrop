import { formatCurrency } from '@/lib/format'

export default function PriceHistoryChart({ history = [] }) {
  if (!history.length) {
    return null
  }

  const prices = history.map((point) => point.price)
  const min = Math.min(...prices)
  const max = Math.max(...prices)
  const spread = max - min || 1

  const points = history
    .map((point, index) => {
      const x = history.length === 1 ? 50 : (index / (history.length - 1)) * 100
      const y = 40 - ((point.price - min) / spread) * 40
      return `${x},${y}`
    })
    .join(' ')

  const latest = history[history.length - 1]
  const earliest = history[0]

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-950 p-5">
      <div className="flex items-start justify-between gap-4 mb-4">
        <div>
          <p className="text-[11px] uppercase tracking-[0.25em] text-red-500 mb-2">Price History</p>
          <h2 className="text-xl font-semibold text-white">Observed markdown path</h2>
        </div>
        <div className="text-right text-sm">
          <p className="text-gray-500">Latest</p>
          <p className="font-semibold text-white">{formatCurrency(latest.price)}</p>
        </div>
      </div>

      <svg viewBox="0 0 100 44" className="w-full overflow-visible">
        <defs>
          <linearGradient id="priceLine" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#f87171" />
            <stop offset="100%" stopColor="#ef4444" />
          </linearGradient>
        </defs>
        <path d="M0 40.5H100" stroke="#1f2937" strokeWidth="0.5" />
        <path d="M0 20.5H100" stroke="#111827" strokeWidth="0.5" />
        <polyline
          fill="none"
          stroke="url(#priceLine)"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          points={points}
        />
      </svg>

      <div className="mt-4 flex items-center justify-between text-sm text-gray-500">
        <div>
          <p>First seen</p>
          <p className="text-white">{formatCurrency(earliest.price)}</p>
        </div>
        <div className="text-right">
          <p>Range</p>
          <p className="text-white">
            {formatCurrency(min)} to {formatCurrency(max)}
          </p>
        </div>
      </div>
    </div>
  )
}
