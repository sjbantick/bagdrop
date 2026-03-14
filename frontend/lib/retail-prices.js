/**
 * Static retail price data for major luxury brands.
 * Sources: brand.com, PurseBlog, Bragmyway price history archives.
 * Updated manually when brands announce price increases.
 */

export const RETAIL_PRICE_HISTORY = [
  // ── Chanel ──
  {
    brand: 'Chanel',
    model: 'Classic Flap Medium',
    size: 'Medium',
    history: [
      { date: '2019-07-01', price: 5800, event: null },
      { date: '2020-05-01', price: 6500, event: 'COVID price increase' },
      { date: '2021-01-01', price: 7800, event: null },
      { date: '2021-07-01', price: 8200, event: null },
      { date: '2022-03-01', price: 8800, event: null },
      { date: '2023-03-01', price: 10200, event: 'March 2023 increase' },
      { date: '2024-03-01', price: 10800, event: 'March 2024 increase' },
      { date: '2024-09-01', price: 11000, event: 'September 2024 increase' },
      { date: '2025-03-01', price: 11500, event: 'March 2025 increase' },
    ],
  },
  {
    brand: 'Chanel',
    model: 'Classic Flap Small',
    size: 'Small',
    history: [
      { date: '2019-07-01', price: 5200, event: null },
      { date: '2020-05-01', price: 5800, event: 'COVID price increase' },
      { date: '2021-01-01', price: 7000, event: null },
      { date: '2022-03-01', price: 7800, event: null },
      { date: '2023-03-01', price: 9200, event: 'March 2023 increase' },
      { date: '2024-03-01', price: 9700, event: 'March 2024 increase' },
      { date: '2025-03-01', price: 10300, event: 'March 2025 increase' },
    ],
  },
  {
    brand: 'Chanel',
    model: 'Boy Bag',
    size: 'Medium',
    history: [
      { date: '2019-07-01', price: 5200, event: null },
      { date: '2020-05-01', price: 5600, event: null },
      { date: '2021-07-01', price: 6300, event: null },
      { date: '2022-03-01', price: 7000, event: null },
      { date: '2023-03-01', price: 7700, event: 'March 2023 increase' },
      { date: '2024-03-01', price: 8200, event: 'March 2024 increase' },
    ],
  },
  {
    brand: 'Chanel',
    model: 'Wallet on Chain',
    size: 'One Size',
    history: [
      { date: '2019-07-01', price: 2100, event: null },
      { date: '2021-01-01', price: 2650, event: null },
      { date: '2022-03-01', price: 3100, event: null },
      { date: '2023-03-01', price: 3500, event: 'March 2023 increase' },
      { date: '2024-03-01', price: 3800, event: 'March 2024 increase' },
    ],
  },

  // ── Hermès ──
  {
    brand: 'Hermès',
    model: 'Birkin 25',
    size: '25',
    history: [
      { date: '2019-01-01', price: 10200, event: null },
      { date: '2020-01-01', price: 10500, event: null },
      { date: '2021-01-01', price: 10900, event: null },
      { date: '2022-01-01', price: 11400, event: 'Annual increase' },
      { date: '2023-01-01', price: 12100, event: 'Annual increase' },
      { date: '2024-01-01', price: 12500, event: 'Annual increase' },
      { date: '2025-01-01', price: 12800, event: 'Annual increase' },
    ],
  },
  {
    brand: 'Hermès',
    model: 'Birkin 30',
    size: '30',
    history: [
      { date: '2019-01-01', price: 11900, event: null },
      { date: '2020-01-01', price: 12100, event: null },
      { date: '2022-01-01', price: 13200, event: 'Annual increase' },
      { date: '2023-01-01', price: 13950, event: 'Annual increase' },
      { date: '2024-01-01', price: 14400, event: 'Annual increase' },
      { date: '2025-01-01', price: 14800, event: 'Annual increase' },
    ],
  },
  {
    brand: 'Hermès',
    model: 'Kelly 25',
    size: '25',
    history: [
      { date: '2019-01-01', price: 9350, event: null },
      { date: '2021-01-01', price: 10300, event: null },
      { date: '2022-01-01', price: 10800, event: null },
      { date: '2023-01-01', price: 11400, event: 'Annual increase' },
      { date: '2024-01-01', price: 11800, event: 'Annual increase' },
      { date: '2025-01-01', price: 12100, event: 'Annual increase' },
    ],
  },

  // ── Louis Vuitton ──
  {
    brand: 'Louis Vuitton',
    model: 'Neverfull MM',
    size: 'MM',
    history: [
      { date: '2019-07-01', price: 1500, event: null },
      { date: '2020-07-01', price: 1690, event: null },
      { date: '2021-07-01', price: 1960, event: null },
      { date: '2022-03-01', price: 2030, event: null },
      { date: '2023-02-01', price: 2200, event: 'February 2023 increase' },
      { date: '2024-02-01', price: 2530, event: 'February 2024 increase' },
    ],
  },
  {
    brand: 'Louis Vuitton',
    model: 'Speedy 25',
    size: '25',
    history: [
      { date: '2019-07-01', price: 1140, event: null },
      { date: '2021-01-01', price: 1390, event: null },
      { date: '2022-03-01', price: 1620, event: null },
      { date: '2023-02-01', price: 1770, event: 'February 2023 increase' },
      { date: '2024-02-01', price: 1950, event: 'February 2024 increase' },
    ],
  },
  {
    brand: 'Louis Vuitton',
    model: 'Pochette Métis',
    size: 'One Size',
    history: [
      { date: '2019-07-01', price: 1830, event: null },
      { date: '2021-01-01', price: 2140, event: null },
      { date: '2022-03-01', price: 2350, event: null },
      { date: '2023-02-01', price: 2570, event: 'February 2023 increase' },
      { date: '2024-02-01', price: 2770, event: 'February 2024 increase' },
    ],
  },
]

/**
 * Compute summary stats for a price history entry.
 */
export function computeRetailStats(entry) {
  const history = entry.history
  const first = history[0]
  const last = history[history.length - 1]
  const totalIncreasePct = ((last.price - first.price) / first.price) * 100
  const yearSpan = (new Date(last.date) - new Date(first.date)) / (365.25 * 24 * 60 * 60 * 1000)
  const annualizedPct = yearSpan > 0 ? totalIncreasePct / yearSpan : 0
  const currentRetail = last.price
  const increaseCount = history.length - 1

  return {
    ...entry,
    currentRetail,
    firstPrice: first.price,
    firstDate: first.date,
    lastDate: last.date,
    totalIncreasePct: Math.round(totalIncreasePct * 10) / 10,
    annualizedPct: Math.round(annualizedPct * 10) / 10,
    increaseCount,
  }
}
