'use client'

import Link from 'next/link'
import { buildOutboundUrl } from '@/lib/api'
import { buildMarketPath } from '@/lib/slug'
import { formatCurrency, formatPercent, platformLabel, titleCase } from '@/lib/format'

export default function ListingCard({ listing }) {
  const dropPct = listing.drop_pct ? formatPercent(listing.drop_pct) : '0.0%'
  const dropAmount = listing.drop_amount || 0
  const originalPrice = listing.original_price || listing.current_price
  const marketPath = buildMarketPath(listing.brand, listing.model)
  const detailPath = `/listings/${listing.id}`
  const platformName = platformLabel(listing.platform)
  const outboundUrl = buildOutboundUrl(listing.id, 'listing_card', 'feed')

  return (
    <div className="bg-gray-900 border border-gray-800 rounded-lg overflow-hidden hover:border-red-500 transition-colors group">
      <Link href={detailPath} className="block">
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

          <div className="absolute top-2 right-2 bg-red-600 text-white px-3 py-1 rounded font-bold text-sm">
            -{dropPct}
          </div>

          <div className="absolute top-2 left-2 bg-black/70 text-gray-300 px-2 py-1 rounded text-xs font-mono">
            {platformName}
          </div>
        </div>

        <div className="p-4">
          <h3 className="font-bold text-sm mb-1 group-hover:text-red-500">
            {listing.brand} {titleCase(listing.model)}
          </h3>

          {listing.size && <p className="text-xs text-gray-400">{listing.size}</p>}
          {listing.color && <p className="text-xs text-gray-400">{listing.color}</p>}

          <div className="mt-3 pt-3 border-t border-gray-800">
            <div className="flex items-baseline justify-between gap-4">
              <div>
                <p className="text-2xl font-bold text-white">{formatCurrency(listing.current_price)}</p>
                {originalPrice !== listing.current_price && (
                  <p className="text-xs text-gray-500 line-through">{formatCurrency(originalPrice)}</p>
                )}
              </div>
              <div className="text-right">
                <p className="text-red-500 font-bold text-sm">-{formatCurrency(dropAmount)}</p>
                <p className="text-xs text-gray-500">
                  {new Date(listing.last_seen).toLocaleDateString()}
                </p>
              </div>
            </div>
          </div>
        </div>
      </Link>

      <div className="flex items-center justify-between gap-3 border-t border-gray-800 px-4 py-3 text-xs">
        <Link href={marketPath} className="text-gray-400 transition-colors hover:text-white">
          View market page
        </Link>
        <a
          href={outboundUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-full border border-gray-700 px-3 py-1 text-gray-300 transition-colors hover:border-red-500 hover:text-red-300"
        >
          View on {platformName}
        </a>
      </div>
    </div>
  )
}
