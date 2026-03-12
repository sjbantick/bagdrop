export const SITE_URL =
  (process.env.NEXT_PUBLIC_SITE_URL || 'https://bagdrop.xyz').replace(/\/+$/, '')

export function absoluteUrl(path = '/') {
  if (!path) {
    return SITE_URL
  }

  if (/^https?:\/\//.test(path)) {
    return path
  }

  return `${SITE_URL}${path.startsWith('/') ? path : `/${path}`}`
}
