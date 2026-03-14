'use client'

import { useState } from 'react'

export default function ShareButton({ title, text }) {
  const [copied, setCopied] = useState(false)

  async function handleShare() {
    const url = window.location.href

    // Use native Web Share API on mobile / Safari
    if (navigator.share) {
      try {
        await navigator.share({ title, text, url })
      } catch {
        // User cancelled — not an error
      }
      return
    }

    // Fallback: copy link to clipboard
    try {
      await navigator.clipboard.writeText(url)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // Last resort: prompt
      window.prompt('Copy this link:', url)
    }
  }

  return (
    <button
      onClick={handleShare}
      className="inline-flex items-center justify-center gap-2 rounded-full border border-stone-300 px-5 py-3 text-sm font-medium text-stone-700 transition-colors hover:border-pink-300 hover:text-pink-600"
    >
      {copied ? (
        <>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="shrink-0">
            <path d="M2 7l3.5 3.5L12 3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          Copied!
        </>
      ) : (
        <>
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" className="shrink-0">
            <path d="M9.5 1.5a2 2 0 1 1 0 4 2 2 0 0 1 0-4zM4.5 4.5a2 2 0 1 1 0 4 2 2 0 0 1 0-4zM9.5 8.5a2 2 0 1 1 0 4 2 2 0 0 1 0-4z" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round"/>
            <path d="M6.4 5.9l1.2-.8M6.4 8.1l1.2.8" stroke="currentColor" strokeWidth="1.25" strokeLinecap="round"/>
          </svg>
          Share
        </>
      )}
    </button>
  )
}
