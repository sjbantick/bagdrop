import './globals.css'
import { SITE_URL } from '@/lib/site'

export const metadata = {
  metadataBase: new URL(SITE_URL),
  // Set NEXT_PUBLIC_GSC_VERIFICATION in Railway to activate Google Search Console verification
  ...(process.env.NEXT_PUBLIC_GSC_VERIFICATION && {
    verification: { google: process.env.NEXT_PUBLIC_GSC_VERIFICATION },
  }),
  title: {
    default: 'BagDrop | Luxury Handbag Price Drops',
    template: '%s | BagDrop',
  },
  description: 'Real-time luxury handbag price drop tracker across Fashionphile, Rebag, The RealReal, and Vestiaire.',
  alternates: {
    canonical: '/',
    types: {
      'application/rss+xml': '/feed.xml',
    },
  },
  openGraph: {
    title: 'BagDrop | Luxury Handbag Price Drops',
    description: 'Real-time luxury handbag price drop tracker across Fashionphile, Rebag, The RealReal, and Vestiaire.',
    url: '/',
    siteName: 'BagDrop',
    type: 'website',
    images: [
      {
        url: '/opengraph-image',
        width: 1200,
        height: 630,
        alt: 'BagDrop luxury handbag price drop tracker',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: 'BagDrop | Luxury Handbag Price Drops',
    description: 'Real-time luxury handbag price drop tracker across Fashionphile, Rebag, The RealReal, and Vestiaire.',
    images: ['/opengraph-image'],
  },
}

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <head>
        {process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN && (
          <script
            defer
            data-domain={process.env.NEXT_PUBLIC_PLAUSIBLE_DOMAIN}
            src="https://plausible.io/js/script.outbound-links.js"
          />
        )}
        <link rel="manifest" href="/manifest.json" />
        <meta name="theme-color" content="#ec4899" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="default" />
        <meta name="apple-mobile-web-app-title" content="BagDrop" />
        <link rel="apple-touch-icon" href="/icon.svg" />
      </head>
      <body className="bg-[#fffdf8] text-stone-900 font-serif">
        {children}
      </body>
    </html>
  )
}
