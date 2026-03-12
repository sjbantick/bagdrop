import Link from 'next/link'

export default function Header({ stats }) {
  return (
    <header className="sticky top-0 z-50 border-b border-stone-200 bg-[#fffdf8]/95 backdrop-blur">
      <div className="mx-auto flex max-w-7xl items-start justify-between gap-4 px-4 py-3 sm:items-center sm:py-4">
        <div className="min-w-0">
          <Link href="/" className="inline-block">
            <h1 className="text-xl font-bold tracking-tighter sm:text-2xl">
              <span className="text-pink-500">BAG</span>
              <span className="text-stone-900">DROP</span>
            </h1>
          </Link>
          <p className="mt-0.5 pr-2 text-[11px] leading-4 text-stone-500 sm:text-xs">
            real-time luxury resale price drops
          </p>
        </div>

        <div className="flex flex-col items-end gap-2 text-[11px] font-mono sm:text-xs">
          <div className="flex items-center gap-3 sm:gap-6">
            <Link href="/" className="text-stone-500 transition-colors hover:text-stone-900">
              feed
            </Link>
            <Link href="/intel" className="text-stone-500 transition-colors hover:text-stone-900">
              intel
            </Link>
          </div>
          <div className="flex flex-wrap items-center justify-end gap-3 sm:gap-6">
            {stats?.total_active_listings > 0 && (
              <span className="text-stone-500">
                {stats.total_active_listings.toLocaleString()} listings
              </span>
            )}
            <div className="flex items-center gap-1.5">
              <span className="inline-block h-1.5 w-1.5 rounded-full bg-green-500 animate-pulse"></span>
              <span className="text-green-500">LIVE</span>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
