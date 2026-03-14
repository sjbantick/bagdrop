'use client'

import { useState } from 'react'
import { getApiUrl } from '@/lib/api'

export default function WatchMarketCard({ brand, model, listingCount }) {
  const [email, setEmail] = useState('')
  const [targetPrice, setTargetPrice] = useState('')
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
          target_price: targetPrice ? parseFloat(targetPrice) : null,
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
      setTargetPrice('')
    } catch (submitError) {
      setError(submitError.message || 'Subscription failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="rounded-2xl border border-stone-200 bg-[#fffaf2] p-5">
      <p className="mb-2 text-[11px] uppercase tracking-[0.25em] text-pink-500">Watch This Market</p>
      <h2 className="text-xl font-semibold text-stone-900">Get the next meaningful drop</h2>
      <p className="mt-3 text-sm leading-7 text-stone-600">
        Get an email when fresh inventory lands in this market instead of checking resale sites manually.
      </p>
      <p className="mt-3 text-sm text-stone-500">
        Current market size: <span className="font-medium text-stone-900">{listingCount}</span> live listings
      </p>

      <form onSubmit={handleSubmit} className="mt-5 space-y-3">
        <label className="block">
          <span className="text-xs text-stone-500">Alert me under $ (optional)</span>
          <input
            type="number"
            min="0"
            step="any"
            value={targetPrice}
            onChange={(event) => setTargetPrice(event.target.value)}
            placeholder="e.g. 3000"
            className="mt-1 w-full rounded-2xl border border-stone-300 bg-white px-4 py-3 text-sm text-stone-900 placeholder:text-stone-400 outline-none transition-colors focus:border-pink-300"
          />
        </label>

        <label className="block">
          <span className="sr-only">Email address</span>
          <input
            type="email"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            placeholder="you@example.com"
            required
            className="w-full rounded-2xl border border-stone-300 bg-white px-4 py-3 text-sm text-stone-900 placeholder:text-stone-400 outline-none transition-colors focus:border-pink-300"
          />
        </label>

        <button
          type="submit"
          disabled={isSubmitting}
          className="inline-flex w-full items-center justify-center rounded-full bg-pink-500 px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-pink-400 disabled:cursor-not-allowed disabled:opacity-60 sm:w-auto"
        >
          {isSubmitting ? 'Saving watch…' : `Email me this market`}
        </button>
      </form>

      {message && <p className="mt-4 text-sm text-green-600">{message}</p>}
      {error && <p className="mt-4 text-sm text-pink-600">{error}</p>}
    </section>
  )
}
