export function slugifyValue(value) {
  return (value || '')
    .normalize('NFKD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'market'
}

export function buildMarketPath(brand, model) {
  return `/${slugifyValue(brand)}/${slugifyValue(model)}`
}
