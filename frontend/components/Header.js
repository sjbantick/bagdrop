import Link from 'next/link'

export default function Header({ stats }) {
  return (
    <header className="sticky top-0 z-50 border-b border-stone-200 bg-[#fffdf8]/95 backdrop-blur">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <div>
          <Link href="/" className="inline-block">
            <h1 className="text-2xl font-bold tracking-tighter">
              <span className="text-pink-500">BAG</span>
              <span className="text-stone-900">DROP</span>
            </h1>
          </Link>
          <p className="mt-0.5 text-xs text-stone-500">real-time luxury resale price drops</p>
        </div>

        <div className="flex items-center gap-6 text-xs font-mono">
          <Link href="/" className="hidden text-stone-500 transition-colors hover:text-stone-900 md:block">
            feed
          </Link>
          <Link href="/intel" className="hidden text-stone-500 transition-colors hover:text-stone-900 md:block">
            intel
          </Link>
          <Link href="/ops" className="hidden text-stone-500 transition-colors hover:text-stone-900 md:block">
            ops
          </Link>
          {stats?.total_active_listings > 0 && (
            <span className="hidden text-stone-500 sm:block">
              {stats.total_active_listings.toLocaleString()} listings
            </span>
          )}
          <div className="flex items-center gap-1.5">
            <span className="inline-block w-1.5 h-1.5 rounded-full bg-green-500 animate-pulse"></span>
            <span className="text-green-500">LIVE</span>
          </div>
        </div>
      </div>
    </header>
  )
}
