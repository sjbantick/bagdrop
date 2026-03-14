export async function GET() {
  const manifest = {
    name: 'BagDrop',
    short_name: 'BagDrop',
    description: 'Luxury handbag price drop tracker',
    start_url: '/',
    display: 'standalone',
    background_color: '#fffdf8',
    theme_color: '#ec4899',
    icons: [
      {
        src: '/icon-192.png',
        sizes: '192x192',
        type: 'image/png',
      },
      {
        src: '/icon-512.png',
        sizes: '512x512',
        type: 'image/png',
      },
    ],
    categories: ['shopping', 'lifestyle'],
    screenshots: [],
  }

  return new Response(JSON.stringify(manifest, null, 2), {
    headers: {
      'Content-Type': 'application/manifest+json',
      'Cache-Control': 'public, max-age=86400',
    },
  })
}
