import './globals.css'
import { SITE_URL } from '@/lib/site'

export const metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: 'BagDrop | Luxury Handbag Price Drops',
    template: '%s | BagDrop',
  },
  description: 'Real-time luxury handbag price drop tracker across Fashionphile, Rebag, The RealReal, and Vestiaire.',
  alternates: {
    canonical: '/',
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
      <body className="bg-black text-white font-sans">
        {children}
      </body>
    </html>
  )
}
