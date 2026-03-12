import { ImageResponse } from 'next/og'
import { fetchApi } from '@/lib/api'
import { formatCurrency, formatPercent, platformLabel, titleCase } from '@/lib/format'

export const size = {
  width: 1200,
  height: 630,
}
export const contentType = 'image/png'

async function getMarket(brand, model) {
  try {
    return await fetchApi(`/api/markets/${brand}/${model}?limit=12`)
  } catch {
    return null
  }
}

export default async function Image({ params }) {
  const market = await getMarket(params.brand, params.model)

  if (!market) {
    return new ImageResponse(
      (
        <div
          style={{
            display: 'flex',
            width: '100%',
            height: '100%',
            alignItems: 'center',
            justifyContent: 'center',
            background: '#050505',
            color: '#ffffff',
            fontFamily: 'sans-serif',
            fontSize: '64px',
            fontWeight: 700,
          }}
        >
          BagDrop Market
        </div>
      ),
      size
    )
  }

  const displayModel = titleCase(market.model)
  const avgDrop = market.stats.average_drop_pct ? `-${formatPercent(market.stats.average_drop_pct)}` : 'Tracked'
  const biggestDrop = market.stats.biggest_drop_pct ? `-${formatPercent(market.stats.biggest_drop_pct)}` : 'N/A'
  const platformLabels = market.platform_breakdown
    .slice(0, 4)
    .map((platform) => platformLabel(platform.platform))
    .join(' • ')

  return new ImageResponse(
    (
      <div
        style={{
          display: 'flex',
          width: '100%',
          height: '100%',
          background: 'linear-gradient(135deg, #050505 0%, #111111 45%, #1f0808 100%)',
          color: '#ffffff',
          padding: '52px',
          fontFamily: 'sans-serif',
        }}
      >
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
            width: '100%',
            border: '1px solid rgba(255,255,255,0.1)',
            borderRadius: '28px',
            padding: '42px',
            background: 'radial-gradient(circle at top right, rgba(239,68,68,0.18), transparent 30%)',
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ fontSize: '22px', letterSpacing: '0.28em', textTransform: 'uppercase', color: '#f87171' }}>
              Canonical Market Page
            </div>
            <div style={{ fontSize: '72px', fontWeight: 700, lineHeight: 1.02, maxWidth: '900px' }}>
              {market.brand} {displayModel}
            </div>
            <div style={{ fontSize: '28px', lineHeight: 1.35, color: '#d1d5db', maxWidth: '860px' }}>
              {market.stats.listing_count} live listings across {market.platform_breakdown.length} platforms. Lowest ask{' '}
              {formatCurrency(market.stats.lowest_price)}.
            </div>
          </div>

          <div style={{ display: 'flex', gap: '18px', alignItems: 'stretch' }}>
            {[
              { label: 'Avg drop', value: avgDrop, accent: '#fca5a5' },
              { label: 'Best drop', value: biggestDrop, accent: '#ef4444' },
              { label: 'Platform mix', value: platformLabels || 'Multi-platform', accent: '#ffffff' },
            ].map((item) => (
              <div
                key={item.label}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  minWidth: item.label === 'Platform mix' ? '420px' : '210px',
                  border: '1px solid rgba(255,255,255,0.12)',
                  borderRadius: '24px',
                  padding: '20px 24px',
                  background: 'rgba(0,0,0,0.3)',
                }}
              >
                <div style={{ fontSize: '20px', color: '#9ca3af' }}>{item.label}</div>
                <div style={{ fontSize: item.label === 'Platform mix' ? '24px' : '42px', fontWeight: 700, color: item.accent }}>
                  {item.value}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    ),
    size
  )
}
