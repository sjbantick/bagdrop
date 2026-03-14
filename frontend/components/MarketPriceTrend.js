'use client'

import { formatCurrency } from '@/lib/format'

function TrendBadge({ direction, pct }) {
  if (!direction || direction === 'stable') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-stone-200 bg-stone-50 px-3 py-1 text-xs font-medium text-stone-600">
        → Stable
      </span>
    )
  }

  if (direction === 'declining') {
    return (
      <span className="inline-flex items-center gap-1 rounded-full border border-green-200 bg-green-50 px-3 py-1 text-xs font-medium text-green-700">
        ↓ Declining{pct != null ? ` ${Math.abs(pct).toFixed(1)}%` : ''}
      </span>
    )
  }

  return (
    <span className="inline-flex items-center gap-1 rounded-full border border-amber-200 bg-amber-50 px-3 py-1 text-xs font-medium text-amber-700">
      ↑ Rising{pct != null ? ` ${Math.abs(pct).toFixed(1)}%` : ''}
    </span>
  )
}

function BuyWaitSignal({ direction, pct, dataPoints }) {
  if (dataPoints < 3) {
    return (
      <div className="rounded-2xl border border-stone-200 bg-stone-50 p-4">
        <p className="text-[11px] uppercase tracking-[0.25em] text-stone-400">Signal</p>
        <p className="mt-2 text-sm text-stone-500">Not enough data yet to generate a signal.</p>
      </div>
    )
  }

  let signal, explanation, tone

  if (direction === 'declining' && pct != null && pct <= -5) {
    signal = 'Buy now'
    explanation = `Prices are dropping ${Math.abs(pct).toFixed(1)}% — sellers are motivated and asking less week over week. Good entry point.`
    tone = 'border-green-200 bg-green-50'
  } else if (direction === 'declining') {
    signal = 'Lean buy'
    explanation = `Prices are trending down modestly. If you see something you like at a good markdown, pull the trigger.`
    tone = 'border-green-200 bg-green-50'
  } else if (direction === 'rising' && pct != null && pct >= 5) {
    signal = 'Wait'
    explanation = `Prices are climbing ${Math.abs(pct).toFixed(1)}% — the market is tightening. Wait for supply to catch up unless you find a steep markdown.`
    tone = 'border-amber-200 bg-amber-50'
  } else if (direction === 'rising') {
    signal = 'Lean wait'
    explanation = `Prices are creeping up. No urgency to buy unless you spot a listing well below average.`
    tone = 'border-amber-200 bg-amber-50'
  } else {
    signal = 'Neutral'
    explanation = `Prices are flat — no clear direction. Buy if you find a good deal, but don't rush.`
    tone = 'border-stone-200 bg-stone-50'
  }

  return (
    <div className={`rounded-2xl border ${tone} p-4`}>
      <p className="text-[11px] uppercase tracking-[0.25em] text-pink-500">Buy / Wait Signal</p>
      <p className="mt-2 text-xl font-semibold text-stone-900">{signal}</p>
      <p className="mt-2 text-sm leading-6 text-stone-600">{explanation}</p>
    </div>
  )
}

export default function MarketPriceTrend({ trend }) {
  if (!trend || !trend.trend || trend.trend.length < 2) {
    return null
  }

  const points = trend.trend
  const prices = points.map((p) => p.avg_price)
  const minPrice = Math.min(...prices)
  const maxPrice = Math.max(...prices)
  const priceRange = maxPrice - minPrice || 1

  // SVG chart dimensions
  const chartWidth = 600
  const chartHeight = 160
  const padding = { top: 10, right: 10, bottom: 24, left: 10 }
  const innerWidth = chartWidth - padding.left - padding.right
  const innerHeight = chartHeight - padding.top - padding.bottom

  const stepX = innerWidth / (points.length - 1)

  // Build SVG path
  const pathPoints = points.map((p, i) => {
    const x = padding.left + i * stepX
    const y = padding.top + innerHeight - ((p.avg_price - minPrice) / priceRange) * innerHeight
    return { x, y, ...p }
  })

  const linePath = pathPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`).join(' ')

  // Area fill path
  const areaPath = `${linePath} L ${pathPoints[pathPoints.length - 1].x.toFixed(1)} ${(padding.top + innerHeight).toFixed(1)} L ${pathPoints[0].x.toFixed(1)} ${(padding.top + innerHeight).toFixed(1)} Z`

  // Format week labels — show first, middle, last
  const labelIndices = [0, Math.floor(points.length / 2), points.length - 1]

  return (
    <div className="space-y-4">
      <div>
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="mb-2 text-[11px] uppercase tracking-[0.25em] text-pink-500">Price Trend</p>
            <h3 className="text-lg font-semibold text-stone-900">90-day market prices</h3>
          </div>
          <TrendBadge direction={trend.trend_direction} pct={trend.trend_pct} />
        </div>

        <div className="mt-3 flex items-center gap-6 text-sm text-stone-500">
          <span>Low: <span className="font-medium text-stone-900">{formatCurrency(minPrice)}</span></span>
          <span>High: <span className="font-medium text-stone-900">{formatCurrency(maxPrice)}</span></span>
          <span>{trend.data_points_total} data points</span>
        </div>
      </div>

      {/* SVG sparkline chart */}
      <div className="rounded-2xl border border-stone-200 bg-white/80 p-4">
        <svg
          viewBox={`0 0 ${chartWidth} ${chartHeight}`}
          className="w-full"
          preserveAspectRatio="none"
          aria-label="Price trend chart"
          role="img"
        >
          <defs>
            <linearGradient id="trendFill" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="rgb(236,72,153)" stopOpacity="0.15" />
              <stop offset="100%" stopColor="rgb(236,72,153)" stopOpacity="0.02" />
            </linearGradient>
          </defs>

          {/* Area fill */}
          <path d={areaPath} fill="url(#trendFill)" />

          {/* Trend line */}
          <path d={linePath} fill="none" stroke="rgb(236,72,153)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />

          {/* Data point dots */}
          {pathPoints.map((p, i) => (
            <circle
              key={i}
              cx={p.x}
              cy={p.y}
              r="3.5"
              fill="white"
              stroke="rgb(236,72,153)"
              strokeWidth="2"
            />
          ))}

          {/* X-axis labels */}
          {labelIndices.map((idx) => {
            const p = pathPoints[idx]
            if (!p) return null
            const dateLabel = new Date(p.week_start + 'T00:00:00').toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
            return (
              <text
                key={idx}
                x={p.x}
                y={chartHeight - 4}
                textAnchor="middle"
                className="fill-stone-400"
                style={{ fontSize: '11px' }}
              >
                {dateLabel}
              </text>
            )
          })}
        </svg>
      </div>

      <BuyWaitSignal
        direction={trend.trend_direction}
        pct={trend.trend_pct}
        dataPoints={points.length}
      />
    </div>
  )
}
