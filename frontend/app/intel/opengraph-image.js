import { ImageResponse } from 'next/og'
import { fetchApi } from '@/lib/api'
import { formatCurrency } from '@/lib/format'

export const size = {
  width: 1200,
  height: 630,
}

export const contentType = 'image/png'

async function getBrief() {
  try {
    return await fetchApi('/api/intelligence/brief')
  } catch {
    return {
      arbitrage: [],
      new_drops: [],
      bag_index_movers: [],
    }
  }
}

export default async function Image() {
  const brief = await getBrief()
  const topArb = brief.arbitrage[0]
  const topMover = brief.bag_index_movers[0]

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
              BagDrop Intelligence
            </div>
            <div style={{ fontSize: '72px', fontWeight: 700, lineHeight: 1.02 }}>
              Daily market brief
            </div>
            <div style={{ fontSize: '28px', lineHeight: 1.35, color: '#d1d5db', maxWidth: '860px' }}>
              Arbitrage, fresh drops, and brand-level price pressure in one owned BagDrop surface.
            </div>
          </div>

          <div style={{ display: 'flex', gap: '18px' }}>
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                minWidth: '360px',
                border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: '24px',
                padding: '20px 24px',
                background: 'rgba(0,0,0,0.3)',
              }}
            >
              <div style={{ fontSize: '20px', color: '#9ca3af' }}>Top arbitrage</div>
              <div style={{ fontSize: '30px', fontWeight: 700 }}>
                {topArb ? `${topArb.listing.brand} ${topArb.listing.model}` : 'Scanning'}
              </div>
              <div style={{ fontSize: '22px', color: '#fca5a5' }}>
                {topArb ? `-${topArb.market_gap_pct}% vs market` : 'Live'}
              </div>
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
              <div style={{ fontSize: '20px', color: '#9ca3af' }}>Top mover</div>
              <div style={{ fontSize: '30px', fontWeight: 700 }}>
                {topMover ? topMover.brand : 'BagIndex'}
              </div>
              <div style={{ fontSize: '22px', color: '#ffffff' }}>
                {topMover ? `${topMover.index_value} index` : 'Live'}
              </div>
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
              <div style={{ fontSize: '20px', color: '#9ca3af' }}>Signals</div>
              <div style={{ fontSize: '42px', fontWeight: 700 }}>{brief.new_drops.length + brief.arbitrage.length}</div>
              <div style={{ fontSize: '22px', color: '#ffffff' }}>
                {topArb ? formatCurrency(topArb.listing.current_price) : 'Fresh'}
              </div>
            </div>
          </div>
        </div>
      </div>
    ),
    size
  )
}
