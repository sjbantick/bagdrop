export default function Header({ stats }) {
  return (
    <header className="border-b border-gray-800 bg-black sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tighter">
            <span className="text-red-500">BAG</span>
            <span className="text-white">DROP</span>
          </h1>
          <p className="text-xs text-gray-500 mt-0.5">real-time luxury resale price drops</p>
        </div>

        <div className="flex items-center gap-6 text-xs font-mono">
          {stats?.total_active_listings > 0 && (
            <span className="text-gray-500 hidden sm:block">
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
