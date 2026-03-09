'use client'

export default function ListingCard({ listing }) {
  const dropPct = listing.drop_pct ? Math.abs(listing.drop_pct).toFixed(1) : 0
  const dropAmount = listing.drop_amount ? Math.abs(listing.drop_amount).toFixed(0) : 0
  const originalPrice = listing.original_price || listing.current_price

  return (
    <a
      href={listing.url}
      target="_blank"
      rel="noopener noreferrer"
      className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden hover:border-red-500 transition-colors group"
    >
      {/* Image placeholder */}
      <div className="bg-gradient-to-b from-gray-800 to-gray-900 aspect-square flex items-center justify-center relative overflow-hidden">
        {listing.photo_url ? (
          <img
            src={listing.photo_url}
            alt={`${listing.brand} ${listing.model}`}
            className="w-full h-full object-cover group-hover:scale-110 transition-transform"
          />
        ) : (
          <div className="text-gray-600 text-center">
            <p className="text-sm">{listing.brand}</p>
            <p className="text-xs text-gray-700">{listing.model}</p>
          </div>
        )}

        {/* Drop badge */}
        <div className="absolute top-2 right-2 bg-red-600 text-white px-3 py-1 rounded font-bold text-sm">
          −{dropPct}%
        </div>

        {/* Platform badge */}
        <div className="absolute top-2 left-2 bg-black/70 text-gray-300 px-2 py-1 rounded text-xs font-mono">
          {listing.platform}
        </div>
      </div>

      {/* Details */}
      <div className="p-4">
        <h3 className="font-bold text-sm mb-1 group-hover:text-red-500">
          {listing.brand} {listing.model}
        </h3>

        {listing.size && <p className="text-xs text-gray-400">{listing.size}</p>}
        {listing.color && <p className="text-xs text-gray-400">{listing.color}</p>}

        <div className="mt-3 pt-3 border-t border-gray-800">
          <div className="flex items-baseline justify-between">
            <div>
              <p className="text-2xl font-bold text-white">${listing.current_price.toFixed(0)}</p>
              {originalPrice !== listing.current_price && (
                <p className="text-xs text-gray-500 line-through">${originalPrice.toFixed(0)}</p>
              )}
            </div>
            <div className="text-right">
              <p className="text-red-500 font-bold text-sm">−${dropAmount}</p>
              <p className="text-xs text-gray-500">
                {new Date(listing.last_seen).toLocaleDateString()}
              </p>
            </div>
          </div>
        </div>
      </div>
    </a>
  )
}
