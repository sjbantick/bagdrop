'use client'

import Link from 'next/link'
import { buildOutboundUrl } from '@/lib/api'
import { buildMarketPath } from '@/lib/slug'
import { formatCurrency, formatPercent, freshnessLabel, platformLabel, titleCase } from '@/lib/format'

export default function ListingCard({ listing }) {
  const dropPct = listing.drop_pct ? formatPercent(listing.drop_pct) : '0.0%'
  const dropAmount = listing.drop_amount || 0
  const originalPrice = listing.original_price || listing.current_price
  const marketPath = buildMarketPath(listing.brand, listing.model)
  const detailPath = `/listings/${listing.id}`
  const platformName = platformLabel(listing.platform)
  const outboundUrl = buildOutboundUrl(listing.id, 'listing_card', 'feed')

  return (
    <div className="group overflow-hidden rounded-[1.25rem] border border-stone-200 bg-[#f6efe4] shadow-[0_10px_30px_rgba(194,168,140,0.12)] transition-colors hover:border-pink-300">
      <Link href={detailPath} className="block">
        <div className="relative flex aspect-square items-center justify-center overflow-hidden bg-gradient-to-b from-[#efe5d7] to-[#f8f3eb]">
          {listing.photo_url ? (
            <img
              src={listing.photo_url}
              alt={`${listing.brand} ${listing.model}`}
              className="w-full h-full object-cover group-hover:scale-110 transition-transform"
            />
          ) : (
            <div className="text-center text-stone-500">
              <p className="text-sm">{listing.brand}</p>
              <p className="text-xs text-stone-600">{listing.model}</p>
            </div>
          )}

          <div className="absolute top-2 right-2 rounded-full bg-pink-500 px-3 py-1 text-sm font-bold text-white">
            -{dropPct}
          </div>

          <div className="absolute top-2 left-2 rounded-full bg-white/90 px-2 py-1 text-xs font-mono text-stone-700">
            {platformName}
          </div>
        </div>

        <div className="p-4">
          <h3 className="mb-1 text-sm font-bold text-stone-900 group-hover:text-pink-500">
            {listing.brand} {titleCase(listing.model)}
          </h3>

          {listing.size && <p className="text-xs text-stone-500">{listing.size}</p>}
          {listing.color && <p className="text-xs text-stone-500">{listing.color}</p>}

          <div className="mt-3 border-t border-stone-200 pt-3">
            <div className="flex items-baseline justify-between gap-4">
              <div>
                <p className="text-2xl font-bold text-stone-900">{formatCurrency(listing.current_price)}</p>
                {originalPrice !== listing.current_price && (
                  <p className="text-xs text-stone-400 line-through">{formatCurrency(originalPrice)}</p>
                )}
              </div>
              <div className="text-right">
                <p className="text-sm font-bold text-pink-600">-{formatCurrency(dropAmount)}</p>
                <p className="text-xs text-stone-500">
                  {freshnessLabel(listing.last_seen)}
                </p>
              </div>
            </div>
          </div>
        </div>
      </Link>

      <div className="flex items-center justify-between gap-3 border-t border-stone-200 px-4 py-3 text-xs">
        <Link href={marketPath} className="text-stone-500 transition-colors hover:text-stone-900">
          View market page
        </Link>
        <a
          href={outboundUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-full border border-stone-300 bg-white px-3 py-1 text-stone-700 transition-colors hover:border-pink-300 hover:text-pink-600"
        >
          View on {platformName}
        </a>
      </div>
    </div>
  )
}
