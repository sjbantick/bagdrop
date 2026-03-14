import Header from '@/components/Header'

export const metadata = {
  title: 'Offline',
  description: 'You are currently offline.',
}

export default function OfflinePage() {
  return (
    <div className="min-h-screen bg-[#fffdf8] text-stone-900 font-serif">
      <Header />
      <main className="flex flex-col items-center justify-center px-4 py-24">
        <div className="max-w-md w-full border border-stone-200 rounded-2xl bg-white px-8 py-12 text-center shadow-sm">
          <div className="flex items-center justify-center w-14 h-14 rounded-full bg-pink-50 border border-pink-100 mx-auto mb-6">
            <svg
              className="w-7 h-7 text-pink-400"
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={1.5}
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                d="M3 3l18 18M8.111 8.111A6.001 6.001 0 0 0 6 12H3m18 0h-3a6 6 0 0 0-6-6m0 0V3m0 3a6 6 0 0 1 5.889 4.111M12 21v-3"
              />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-stone-900 mb-3 tracking-tight">
            You&rsquo;re offline.
          </h1>
          <p className="text-stone-500 text-base leading-relaxed">
            Check your connection and try again.
          </p>
          <button
            onClick={() => window.location.reload()}
            className="mt-8 inline-flex items-center gap-2 px-6 py-2.5 rounded-full bg-pink-500 hover:bg-pink-600 text-white text-sm font-medium transition-colors"
          >
            Try again
          </button>
        </div>
      </main>
    </div>
  )
}
