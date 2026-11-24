const AMOUNT = /^(\d{1,12})(?:\.(\d{1,2}))?$/

/** Turn a typed dollar amount ("12", "12.5", "$1,200.05") into integer cents; null when it is not a plain amount with at most two decimals. */
export function parseCents(text: string): number | null {
  const match = AMOUNT.exec(text.trim().replace(/^\$/, '').replaceAll(',', ''))
  if (!match) return null
  return Number(match[1]) * 100 + Number((match[2] ?? '').padEnd(2, '0'))
}

const USD = new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' })

/** Format integer cents as US dollars, for example 123456 as "$1,234.56". */
export function formatUsd(cents: number): string {
  return USD.format(cents / 100)
}
