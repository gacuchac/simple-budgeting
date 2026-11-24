import type { Category, LimitStatus } from '../api/client'
import { formatUsd } from '../money'

type Props = { limits: LimitStatus[]; categories: Category[] }

/** One marker (icon, label and amounts) per category over its limit; nothing when none is over. */
export function OverLimitList({ limits, categories }: Props) {
  const over = limits.filter((l) => l.over)
  if (over.length === 0) return null
  const name = (id: number) => categories.find((c) => c.id === id)?.name ?? 'Category'
  return (
    <ul className="over-limits" aria-label="Categories over limit">
      {over.map((l) => (
        <li key={l.limit_id} className="limit-note">
          <span aria-hidden="true">▲</span>
          <strong>Over limit</strong>
          <span>{name(l.category_id)}: {formatUsd(l.spent_cents)} of {formatUsd(l.allowed_cents)} allowed</span>
        </li>
      ))}
    </ul>
  )
}
