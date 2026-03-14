import { ImageResponse } from 'next/og'

export const alt = 'BagDrop luxury handbag price drop tracker'
export const size = {
  width: 1200,
  height: 630,
}
export const contentType = 'image/png'

export default function Image() {
  return new ImageResponse(
    (
      <div
        style={{
          display: 'flex',
          width: '100%',
          height: '100%',
          background: 'linear-gradient(135deg, #050505 0%, #111111 45%, #260505 100%)',
          color: '#ffffff',
          padding: '56px',
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
            padding: '44px',
            background: 'radial-gradient(circle at top right, rgba(236,72,153,0.16), transparent 28%)',
          }}
        >
          <div style={{ display: 'flex', flexDirection: 'column', gap: '18px' }}>
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '14px',
                fontSize: '24px',
                letterSpacing: '0.32em',
                textTransform: 'uppercase',
                color: '#ec4899',
              }}
            >
              <div
                style={{
                  width: '14px',
                  height: '14px',
                  borderRadius: '9999px',
                  background: '#ec4899',
                }}
              />
              BagDrop
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', maxWidth: '780px' }}>
              <div style={{ fontSize: '76px', fontWeight: 700, lineHeight: 1.02 }}>
                Luxury handbag price drops.
              </div>
              <div style={{ fontSize: '30px', lineHeight: 1.35, color: '#d1d5db' }}>
                Track resale prices across Fashionphile, Rebag, The RealReal, and Vestiaire — updated hourly.
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '18px' }}>
            {[
              'Price drop alerts',
              'Cross-platform comparison',
              'Buy / wait signals',
            ].map((label) => (
              <div
                key={label}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  border: '1px solid rgba(255,255,255,0.12)',
                  borderRadius: '9999px',
                  padding: '16px 22px',
                  fontSize: '22px',
                  color: '#e5e7eb',
                  background: 'rgba(0,0,0,0.32)',
                }}
              >
                {label}
              </div>
            ))}
          </div>
        </div>
      </div>
    ),
    size
  )
}
