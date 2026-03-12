import { normalizeBaseUrl } from '@/lib/api'

export const SITE_URL = normalizeBaseUrl(process.env.NEXT_PUBLIC_SITE_URL, 'https://thebagdrop.xyz')

export function absoluteUrl(path = '/') {
  if (!path) {
    return SITE_URL
  }

  if (/^https?:\/\//.test(path)) {
    return path
  }

  return `${SITE_URL}${path.startsWith('/') ? path : `/${path}`}`
}
