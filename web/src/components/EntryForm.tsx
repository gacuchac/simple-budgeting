import { useState, type FormEvent } from 'react'
import type { Category, Entry, EntryIn } from '../api/client'
import { today as todayIso } from '../dates'
import { useAddEntry, useReplaceEntry, useSplitEntry } from '../hooks/useWrites'
import { parseCents } from '../money'
import { fromRule, toRule, type RuleForm } from '../rule'
import { RuleEditor } from './RuleEditor'

type Props = {
  budgetId: number
  kind: 'income' | 'expense'
  categories: Category[]
  entry?: Entry
  onDone: () => void
  onCancel: () => void
}

function centsText(cents: number): string {
  return `${Math.floor(cents / 100)}.${String(cents % 100).padStart(2, '0')}`
}

export function EntryForm({ budgetId, kind, categories, entry, onDone, onCancel }: Props) {
  const today = todayIso()
  const recurring = entry !== undefined && entry.rule.type !== 'one_off'
  const options = categories.filter((c) => c.kind === kind)
  const [name, setName] = useState(entry?.name ?? '')
  const [amount, setAmount] = useState(entry ? centsText(entry.amount_cents) : '')
  const [source, setSource] = useState(entry?.source ?? '')
  const [categoryId, setCategoryId] = useState<number | null>(entry ? (entry.category_id ?? null) : kind === 'income' ? (options[0]?.id ?? null) : null)
  const [rule, setRule] = useState<RuleForm>(entry ? fromRule(entry.rule) : { shape: 'one_off', date: today })
  const [at, setAt] = useState(today)
  const [problem, setProblem] = useState<string | null>(null)
  const add = useAddEntry()
  const replace = useReplaceEntry()
  const split = useSplitEntry()
  const write = entry ? (recurring ? split : replace) : add
  const error = problem ?? write.error

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    const cents = parseCents(amount)
    const parsedRule = toRule(rule)
    if (cents === null || cents <= 0) return setProblem('Enter an amount above zero with at most two decimals.')
    if (parsedRule === null) return setProblem('Fill in every field of the rule.')
    setProblem(null)
    const body: EntryIn = {
      kind,
      name: name.trim(),
      amount_cents: cents,
      category_id: categoryId,
      source: kind === 'income' ? source.trim() || null : null,
      rule: parsedRule,
    }
    let saved: unknown
    if (!entry) saved = await add.run(budgetId, body)
    else if (recurring && parsedRule.type !== 'one_off') {
      saved = await split.run(budgetId, entry.id, at, {
        name: body.name,
        amount_cents: body.amount_cents,
        category_id: body.category_id,
        source: body.source,
        rule: parsedRule,
      })
    } else saved = await replace.run(budgetId, entry.id, body)
    if (saved !== null) onDone()
  }

  return (
    <form role="dialog" aria-label={`${entry ? 'Edit' : 'Add'} ${kind}`} onSubmit={onSubmit}>
      <label>Name <input value={name} onChange={(e) => setName(e.target.value)} required /></label>
      <label>Amount (USD) <input inputMode="decimal" value={amount} onChange={(e) => setAmount(e.target.value)} required /></label>
      {kind === 'income' && <label>Source <input value={source} onChange={(e) => setSource(e.target.value)} /></label>}
      <label>
        Category{' '}
        <select value={categoryId ?? ''} onChange={(e) => setCategoryId(e.target.value === '' ? null : Number(e.target.value))}>
          {kind === 'expense' && <option value="">None</option>}
          {options.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
        </select>
      </label>
      <RuleEditor value={rule} onChange={setRule} allowOneOff={!recurring} today={today} />
      {recurring && <label>Apply changes from <input type="date" value={at} onChange={(e) => setAt(e.target.value)} required /></label>}
      {error && <p role="alert">{error}</p>}
      <button type="submit" disabled={write.busy}>Save</button>
      <button type="button" onClick={onCancel}>Cancel</button>
    </form>
  )
}
