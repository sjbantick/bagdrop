import { ImageResponse } from 'next/og'
import { RETAIL_PRICE_HISTORY, computeRetailStats } from '@/lib/retail-prices'

export const size = {
  width: 1200,
  height: 630,
}

export const contentType = 'image/png'

export default async function Image() {
  const entries = RETAIL_PRICE_HISTORY.map(computeRetailStats)
  const avgTotalIncrease = Math.round(
    entries.reduce((sum, e) => sum + e.totalIncreasePct, 0) / entries.length
  )
  const maxEntry = entries.reduce((max, e) => (e.totalIncreasePct > max.totalIncreasePct ? e : max), entries[0])

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
              BagDrop Intel
            </div>
            <div style={{ fontSize: '68px', fontWeight: 700, lineHeight: 1.02 }}>
              Retail price tracker
            </div>
            <div style={{ fontSize: '26px', lineHeight: 1.35, color: '#d1d5db', maxWidth: '860px' }}>
              Every Chanel, Hermès, and Louis Vuitton price increase since 2019.
            </div>
          </div>

          <div style={{ display: 'flex', gap: '18px' }}>
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
              <div style={{ fontSize: '20px', color: '#9ca3af' }}>Avg increase</div>
              <div style={{ fontSize: '46px', fontWeight: 700, color: '#ec4899' }}>+{avgTotalIncrease}%</div>
              <div style={{ fontSize: '18px', color: '#9ca3af' }}>since 2019</div>
            </div>

            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                minWidth: '320px',
                border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: '24px',
                padding: '20px 24px',
                background: 'rgba(0,0,0,0.3)',
              }}
            >
              <div style={{ fontSize: '20px', color: '#9ca3af' }}>Biggest increase</div>
              <div style={{ fontSize: '36px', fontWeight: 700 }}>
                {maxEntry.brand} {maxEntry.model}
              </div>
              <div style={{ fontSize: '22px', color: '#ec4899' }}>+{maxEntry.totalIncreasePct}%</div>
            </div>

            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                minWidth: '200px',
                border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: '24px',
                padding: '20px 24px',
                background: 'rgba(0,0,0,0.3)',
              }}
            >
              <div style={{ fontSize: '20px', color: '#9ca3af' }}>Models</div>
              <div style={{ fontSize: '46px', fontWeight: 700 }}>{entries.length}</div>
              <div style={{ fontSize: '18px', color: '#9ca3af' }}>tracked</div>
            </div>
          </div>
        </div>
      </div>
    ),
    size
  )
}
