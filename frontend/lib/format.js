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
    yoogi: "Yoogi's Closet",
    luxedh: 'LuxeDH',
    madisonavenuecouture: 'Madison Avenue Couture',
  }

  return labels[platform] || platform
}

export function freshnessLabel(value) {
  if (!value) {
    return 'Freshness unknown'
  }

  const timestamp = new Date(value)
  if (Number.isNaN(timestamp.getTime())) {
    return 'Freshness unknown'
  }

  const deltaHours = Math.max((Date.now() - timestamp.getTime()) / 3600000, 0)
  if (deltaHours < 1) {
    return 'Verified this hour'
  }
  if (deltaHours < 24) {
    return `Verified ${Math.round(deltaHours)}h ago`
  }
  return `Verified ${Math.round(deltaHours / 24)}d ago`
}
