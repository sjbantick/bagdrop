export function formatCurrency(value) {
  if (value == null || Number.isNaN(Number(value))) {
    return 'N/A'
  }

  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    maximumFractionDigits: 0,
  }).format(value)
}

export function formatPercent(value, digits = 1) {
  if (value == null || Number.isNaN(Number(value))) {
    return null
  }

  return `${Number(value).toFixed(digits)}%`
}

export function titleCase(value) {
  return (value || '')
    .split(/\s+/)
    .filter(Boolean)
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

export function platformLabel(platform) {
  const labels = {
    fashionphile: 'Fashionphile',
    rebag: 'Rebag',
    realreal: 'The RealReal',
    vestiaire: 'Vestiaire',
  }

  return labels[platform] || platform
}
