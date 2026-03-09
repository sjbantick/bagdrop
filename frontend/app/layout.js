import './globals.css'

export const metadata = {
  title: 'BagDrop — Luxury Handbag Price Drops',
  description: 'Real-time price drop tracker for Hermès, Chanel, Louis Vuitton and more',
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
