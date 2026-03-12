import Link from 'next/link'

export default function NotFound() {
  return (
    <div className="min-h-screen bg-black text-white flex items-center justify-center px-4">
      <div className="max-w-lg text-center">
        <p className="text-[11px] uppercase tracking-[0.3em] text-red-500 mb-4">404</p>
        <h1 className="text-4xl font-semibold">Page not found</h1>
        <p className="mt-4 text-gray-400 leading-7">
          This BagDrop page does not have enough live inventory yet, or the URL does not map to a tracked market.
        </p>
        <Link
          href="/"
          className="inline-flex mt-8 rounded-full bg-red-600 px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-red-500"
        >
          Back to live feed
        </Link>
      </div>
    </div>
  )
}
