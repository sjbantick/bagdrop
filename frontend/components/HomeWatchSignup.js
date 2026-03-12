'use client'

import { useEffect, useMemo, useState } from 'react'
import { getApiUrl } from '@/lib/api'
import { titleCase } from '@/lib/format'

function optionLabel(market) {
  return `${market.brand} ${titleCase(market.model)}`
}

export default function HomeWatchSignup({ markets = [] }) {
  const fallbackMarket = useMemo(
    () => (markets.length ? markets[0] : { brand: 'Chanel', model: 'classic flap' }),
    [markets]
  )

  const [email, setEmail] = useState('')
  const [marketValue, setMarketValue] = useState(optionLabel(fallbackMarket))
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    if (!marketValue && fallbackMarket) {
      setMarketValue(optionLabel(fallbackMarket))
    }
  }, [fallbackMarket, marketValue])

  const selectedMarket = useMemo(() => {
    const normalized = marketValue.trim().toLowerCase()
    return markets.find((market) => optionLabel(market).toLowerCase() === normalized) || fallbackMarket
  }, [fallbackMarket, marketValue, markets])

  const handleSubmit = async (event) => {
    event.preventDefault()
    setMessage('')
    setError('')
    setIsSubmitting(true)

    try {
      const response = await fetch(getApiUrl('/api/watchlists'), {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email,
          brand: selectedMarket.brand,
          model: titleCase(selectedMarket.model),
          source: 'homepage_hero',
        }),
      })

      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.detail || 'Subscription failed')
      }

      setMessage(
        payload.already_subscribed
          ? `Already watching ${selectedMarket.brand} ${titleCase(selectedMarket.model)}.`
          : `Watching ${selectedMarket.brand} ${titleCase(selectedMarket.model)}.`
      )
      setEmail('')
    } catch (submitError) {
      setError(submitError.message || 'Subscription failed')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section className="mb-8 rounded-3xl border border-stone-200 bg-[#fffaf2] p-5 shadow-[0_12px_30px_rgba(194,168,140,0.08)] sm:p-6">
      <div className="grid gap-5 lg:grid-cols-[0.9fr_1.1fr] lg:items-end">
        <div>
          <p className="mb-2 text-[11px] uppercase tracking-[0.25em] text-pink-500">Email Alerts</p>
          <h2 className="text-2xl font-semibold text-stone-900">Get fresh drops in your inbox</h2>
          <p className="mt-3 max-w-2xl text-sm leading-7 text-stone-600">
            Pick a market and BagDrop will email you when new inventory lands instead of making you check resale sites manually.
          </p>
        </div>

        <form onSubmit={handleSubmit} className="grid gap-3 sm:grid-cols-[1fr_1fr_auto]">
          <label className="block">
            <span className="sr-only">Market</span>
            <input
              type="text"
              list="homepage-watch-markets"
              value={marketValue}
              onChange={(event) => setMarketValue(event.target.value)}
              placeholder="Choose a market"
              className="w-full rounded-2xl border border-stone-300 bg-white px-4 py-3 text-sm text-stone-900 placeholder:text-stone-400 outline-none transition-colors focus:border-pink-300"
            />
            <datalist id="homepage-watch-markets">
              {markets.map((market) => (
                <option key={market.canonical_path} value={optionLabel(market)} />
              ))}
            </datalist>
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
            className="inline-flex items-center justify-center rounded-full bg-pink-500 px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-pink-400 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? 'Saving…' : 'Start watching'}
          </button>
        </form>
      </div>

      {message && <p className="mt-4 text-sm text-green-600">{message}</p>}
      {error && <p className="mt-4 text-sm text-pink-600">{error}</p>}
    </section>
  )
}
