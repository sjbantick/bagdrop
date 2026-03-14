import { ImageResponse } from 'next/og'
import { fetchApi } from '@/lib/api'

export const size = {
  width: 1200,
  height: 630,
}

export const contentType = 'image/png'

export default async function Image() {
  let markets = []
  try {
    markets = await fetchApi('/api/markets/featured?limit=48&min_listings=1')
  } catch {}

  const brandSet = new Set(markets.map((m) => m.brand))
  const totalListings = markets.reduce((sum, m) => sum + m.listing_count, 0)
  const biggestDrop = Math.max(...markets.map((m) => m.biggest_drop_pct || 0), 0)

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
            background: 'radial-gradient(circle at top right, rgba(236,72,153,0.18), transparent 30%)',
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ fontSize: '22px', letterSpacing: '0.28em', textTransform: 'uppercase', color: '#ec4899' }}>
              BagDrop
            </div>
            <div style={{ fontSize: '72px', fontWeight: 700, lineHeight: 1.02 }}>
              All markets
            </div>
            <div style={{ fontSize: '28px', lineHeight: 1.35, color: '#d1d5db', maxWidth: '860px' }}>
              Browse every luxury handbag market tracked by BagDrop across 9+ resale platforms.
            </div>
          </div>

          <div style={{ display: 'flex', gap: '18px' }}>
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                minWidth: '260px',
                border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: '24px',
                padding: '20px 24px',
                background: 'rgba(0,0,0,0.3)',
              }}
            >
              <div style={{ fontSize: '20px', color: '#9ca3af' }}>Brands</div>
              <div style={{ fontSize: '46px', fontWeight: 700 }}>{brandSet.size}</div>
              <div style={{ fontSize: '18px', color: '#9ca3af' }}>tracked</div>
            </div>

            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                minWidth: '260px',
                border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: '24px',
                padding: '20px 24px',
                background: 'rgba(0,0,0,0.3)',
              }}
            >
              <div style={{ fontSize: '20px', color: '#9ca3af' }}>Models</div>
              <div style={{ fontSize: '46px', fontWeight: 700 }}>{markets.length}</div>
              <div style={{ fontSize: '18px', color: '#9ca3af' }}>markets</div>
            </div>

            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                minWidth: '280px',
                border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: '24px',
                padding: '20px 24px',
                background: 'rgba(0,0,0,0.3)',
              }}
            >
              <div style={{ fontSize: '20px', color: '#9ca3af' }}>Active listings</div>
              <div style={{ fontSize: '46px', fontWeight: 700 }}>{totalListings.toLocaleString()}</div>
              <div style={{ fontSize: '18px', color: '#ec4899' }}>
                {biggestDrop > 0 ? `up to -${biggestDrop.toFixed(0)}% off` : 'live'}
              </div>
            </div>
          </div>
        </div>
      </div>
    ),
    size
  )
}
