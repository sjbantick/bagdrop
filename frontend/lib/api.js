const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export function getApiUrl(path) {
  return `${API_URL}${path}`
}

export async function fetchApi(path, options = {}) {
  const response = await fetch(getApiUrl(path), {
    cache: 'no-store',
    ...options,
  })

  if (!response.ok) {
    throw new Error(`API request failed: ${response.status} ${path}`)
  }

  return response.json()
}

export function buildOutboundUrl(listingId, surface, context = '') {
  const params = new URLSearchParams({ surface })
  if (context) {
    params.set('context', context)
  }

  return getApiUrl(`/api/listings/${listingId}/outbound?${params.toString()}`)
}

export { API_URL }
