import type { LimitStatus } from '../api/client'
import { formatUsd } from '../money'

/** The "Over limit" notice for a limit status; renders nothing unless `status.over`. */
export function LimitWarning({ status }: { status: LimitStatus | null }) {
  if (!status?.over) return null
  return (
    <p className="limit-note" role="status">
      <span aria-hidden="true">▲</span>
      <strong>Over limit</strong>
      <span>{formatUsd(status.spent_cents)} of {formatUsd(status.allowed_cents)} allowed</span>
    </p>
  )
}
