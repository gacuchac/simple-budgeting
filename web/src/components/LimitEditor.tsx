import { useState, type FormEvent } from 'react'
import type { Limit, PeriodUnit } from '../api/client'
import { useDeleteLimit, useSetLimit } from '../hooks/useWrites'
import { formatUsd, parseCents } from '../money'

const PERIODS: PeriodUnit[] = ['day', 'week', 'month', 'year']

type Props = { budgetId: number; categoryId: number; limit: Limit | undefined; onChanged: () => void }

function centsText(cents: number): string {
  return `${Math.floor(cents / 100)}.${String(cents % 100).padStart(2, '0')}`
}

/** Set, change or clear the spending limit of one expense category. */
export function LimitEditor({ budgetId, categoryId, limit, onChanged }: Props) {
  const [amount, setAmount] = useState(limit ? centsText(limit.amount_cents) : '')
  const [period, setPeriod] = useState<PeriodUnit>(limit?.period ?? 'month')
  const [problem, setProblem] = useState<string | null>(null)
  const set = useSetLimit()
  const clear = useDeleteLimit()
  const onSave = async (event: FormEvent) => {
    event.preventDefault()
    const cents = parseCents(amount)
    if (cents === null || cents <= 0) return setProblem('Enter an amount above zero with at most two decimals.')
    setProblem(null)
    if ((await set.run(budgetId, { category_id: categoryId, amount_cents: cents, period })) !== null) onChanged()
  }
  const onClear = async () => {
    if (limit && (await clear.run(budgetId, limit.id)) !== null) {
      setAmount('')
      onChanged()
    }
  }
  const error = problem ?? set.error ?? clear.error
  return (
    <form className="limit-editor" onSubmit={onSave}>
      <input aria-label="Limit amount (USD)" inputMode="decimal" placeholder="No limit" value={amount} onChange={(e) => setAmount(e.target.value)} />
      <select aria-label="Limit period" value={period} onChange={(e) => setPeriod(e.target.value as PeriodUnit)}>
        {PERIODS.map((p) => <option key={p} value={p}>per {p}</option>)}
      </select>
      <button type="submit" disabled={set.busy}>{limit ? 'Change' : 'Set limit'}</button>
      {limit && <button type="button" className="ghost" onClick={onClear} disabled={clear.busy}>Clear</button>}
      {limit && <span className="limit-current">Limit {formatUsd(limit.amount_cents)} per {limit.period}</span>}
      {error && <span className="alert" role="alert">{error}</span>}
    </form>
  )
}
