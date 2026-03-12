import { ImageResponse } from 'next/og'
import { fetchApi } from '@/lib/api'
import { formatCurrency, formatPercent, platformLabel, titleCase } from '@/lib/format'

export const size = {
  width: 1200,
  height: 630,
}
export const contentType = 'image/png'

async function getListing(listingId) {
  try {
    return await fetchApi(`/api/listings/${listingId}`)
  } catch {
    return null
  }
}

export default async function Image({ params }) {
  const listing = await getListing(params.listingId)

  if (!listing) {
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
          BagDrop Listing
        </div>
      ),
      size
    )
  }

  const displayModel = titleCase(listing.model)
  const platformName = platformLabel(listing.platform)
  const dropPct = listing.drop_pct ? `-${formatPercent(listing.drop_pct)}` : 'Tracked'
  const dropAmount = listing.drop_amount ? `-${formatCurrency(listing.drop_amount)}` : 'N/A'

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
          <div style={{ display: 'flex', justifyContent: 'space-between', gap: '28px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '14px', maxWidth: '760px' }}>
              <div style={{ fontSize: '22px', letterSpacing: '0.28em', textTransform: 'uppercase', color: '#f87171' }}>
                {platformName}
              </div>
              <div style={{ fontSize: '70px', fontWeight: 700, lineHeight: 1.02 }}>
                {listing.brand} {displayModel}
              </div>
              <div style={{ fontSize: '28px', lineHeight: 1.35, color: '#d1d5db' }}>
                Current ask {formatCurrency(listing.current_price)}
                {listing.original_price && listing.original_price !== listing.current_price
                  ? `, previously ${formatCurrency(listing.original_price)}.`
                  : '.'}
              </div>
            </div>

            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                minWidth: '250px',
                border: '1px solid rgba(255,255,255,0.12)',
                borderRadius: '24px',
                padding: '24px',
                background: 'rgba(0,0,0,0.32)',
              }}
            >
              <div style={{ fontSize: '18px', color: '#9ca3af', textTransform: 'uppercase', letterSpacing: '0.18em' }}>
                Condition
              </div>
              <div style={{ fontSize: '36px', fontWeight: 700 }}>{titleCase(listing.condition)}</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '18px' }}>
            {[
              { label: 'Drop', value: dropPct, accent: '#ef4444' },
              { label: 'Markdown', value: dropAmount, accent: '#fca5a5' },
              { label: 'Color', value: titleCase(listing.color || 'Not listed'), accent: '#ffffff' },
              { label: 'Size', value: titleCase(listing.size || 'Not listed'), accent: '#ffffff' },
            ].map((item) => (
              <div
                key={item.label}
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  minWidth: '220px',
                  border: '1px solid rgba(255,255,255,0.12)',
                  borderRadius: '24px',
                  padding: '20px 24px',
                  background: 'rgba(0,0,0,0.3)',
                }}
              >
                <div style={{ fontSize: '20px', color: '#9ca3af' }}>{item.label}</div>
                <div style={{ fontSize: '38px', fontWeight: 700, color: item.accent }}>{item.value}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    ),
    size
  )
}
