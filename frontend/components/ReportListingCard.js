'use client'

import { useState } from 'react'
import { getApiUrl } from '@/lib/api'

export default function ReportListingCard({ listingId }) {
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isHidden, setIsHidden] = useState(false)

  const handleReport = async () => {
    setError('')
    setMessage('')
    setIsSubmitting(true)

    try {
      const response = await fetch(getApiUrl(`/api/listings/${listingId}/report`), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          reason: 'sold',
          source: 'listing_detail',
        }),
      })

      const payload = await response.json()

      if (!response.ok) {
        throw new Error(payload.detail || 'Report failed')
      }

      setMessage(payload.detail)
      setIsHidden(Boolean(payload.listing_hidden))
    } catch (submitError) {
      setError(submitError.message || 'Report failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="rounded-2xl border border-stone-200 bg-[#fffaf2] p-5">
      <p className="mb-2 text-[11px] uppercase tracking-[0.25em] text-pink-500">Trust Signal</p>
      <h2 className="text-xl font-semibold text-stone-900">Seen this bag sold already?</h2>
      <p className="mt-3 text-sm leading-7 text-stone-600">
        Report dead listings and BagDrop will quarantine suspicious inventory faster than the scrape loop alone.
      </p>

      <button
        type="button"
        onClick={handleReport}
        disabled={isSubmitting || isHidden}
        className="mt-5 inline-flex items-center rounded-full border border-stone-300 bg-white px-5 py-3 text-sm font-medium text-stone-700 transition-colors hover:border-pink-300 hover:text-pink-600 disabled:cursor-not-allowed disabled:opacity-60"
      >
        {isHidden ? 'Listing hidden from feed' : isSubmitting ? 'Reporting…' : 'Report sold / dead listing'}
      </button>

      {message && <p className="mt-4 text-sm text-green-600">{message}</p>}
      {error && <p className="mt-4 text-sm text-pink-600">{error}</p>}
    </section>
  )
}
