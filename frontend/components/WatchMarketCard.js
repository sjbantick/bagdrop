'use client'

import { useState } from 'react'
import { getApiUrl } from '@/lib/api'

export default function WatchMarketCard({ brand, model, listingCount }) {
  const [email, setEmail] = useState('')
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    setError('')
    setMessage('')
    setIsSubmitting(true)

    try {
      const response = await fetch(getApiUrl('/api/watchlists'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email,
          brand,
          model,
          source: 'market_page',
        }),
      })

      const payload = await response.json()

      if (!response.ok) {
        throw new Error(payload.detail || 'Subscription failed')
      }

      setMessage(
        payload.already_subscribed
          ? `Already watching ${brand} ${model}.`
          : `Watching ${brand} ${model}. First alert loop is now captured.`
      )
      setEmail('')
    } catch (submitError) {
      setError(submitError.message || 'Subscription failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="rounded-2xl border border-gray-800 bg-gradient-to-br from-gray-950 via-black to-gray-950 p-5">
      <p className="text-[11px] uppercase tracking-[0.25em] text-red-500 mb-2">Watch This Market</p>
      <h2 className="text-xl font-semibold text-white">Get the next meaningful drop</h2>
      <p className="mt-3 text-sm leading-7 text-gray-300">
        BagDrop is not sending alerts yet, but this captures real watch intent now so the first retention loop is built
        on actual demand instead of guesswork.
      </p>
      <p className="mt-3 text-sm text-gray-500">
        Current market size: <span className="text-white">{listingCount}</span> live listings
      </p>

      <form onSubmit={handleSubmit} className="mt-5 space-y-3">
        <label className="block">
          <span className="sr-only">Email address</span>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@example.com"
            required
            className="w-full rounded-2xl border border-gray-700 bg-black px-4 py-3 text-sm text-white placeholder:text-gray-600 outline-none transition-colors focus:border-red-500"
          />
        </label>

        <button
          type="submit"
          disabled={isSubmitting}
          className="inline-flex items-center rounded-full bg-red-600 px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-red-500 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {isSubmitting ? 'Saving watch…' : `Watch ${brand} ${model}`}
        </button>
      </form>

      {message && <p className="mt-4 text-sm text-green-400">{message}</p>}
      {error && <p className="mt-4 text-sm text-red-400">{error}</p>}
    </section>
  )
}
