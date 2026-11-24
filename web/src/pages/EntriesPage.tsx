import { useState } from 'react'
import type { Entry } from '../api/client'
import { EntryForm } from '../components/EntryForm'
import { useBudget } from '../hooks/useBudget'
import { useCategories } from '../hooks/useCategories'
import { useEntries } from '../hooks/useEntries'
import { useDeleteEntry } from '../hooks/useWrites'
import { formatUsd } from '../money'
import { describeRule } from '../rule'

type Editing = { kind: 'income' | 'expense'; entry?: Entry } | null

function EntryRow({ entry, categoryName, canEdit, onEdit, onDelete }: {
  entry: Entry
  categoryName: string
  canEdit: boolean
  onEdit: () => void
  onDelete: () => void
}) {
  return (
    <li>
      <div className="row-main">
        <div className="row-name">{entry.name}</div>
        <div className="row-sub">
          {categoryName}
          {entry.source ? ` · from ${entry.source}` : ''} · {describeRule(entry.rule)}
        </div>
      </div>
      <div className="row-amount">{formatUsd(entry.amount_cents)}</div>
      {canEdit && (
        <div className="row-actions">
          <button className="ghost" onClick={onEdit}>Edit</button>
          <button className="ghost danger" onClick={onDelete}>Delete</button>
        </div>
      )}
    </li>
  )
}

export function EntriesPage() {
  const { budget, canEdit } = useBudget()
  const entries = useEntries(budget.id)
  const categories = useCategories(budget.id)
  const remove = useDeleteEntry()
  const [editing, setEditing] = useState<Editing>(null)

  if (entries.loading || categories.loading) return <p className="status-message">Loading...</p>
  if (entries.error || categories.error) return <p className="status-message alert" role="alert">{(entries.error ?? categories.error)?.message}</p>

  const names = new Map((categories.data ?? []).map((c) => [c.id, c.name]))
  const done = () => {
    setEditing(null)
    entries.reload()
  }
  const onDelete = async (entry: Entry) => {
    if (window.confirm(`Delete "${entry.name}" and its whole series?`) && (await remove.run(budget.id, entry.id)) !== null) entries.reload()
  }

  return (
    <div className="cols">
      {(['income', 'expense'] as const).map((kind) => {
        const rows = (entries.data ?? []).filter((e) => e.kind === kind)
        return (
          <section className="card" key={kind}>
            <div className="card-head">
              <h2>{kind === 'income' ? 'Income' : 'Expenses'}</h2>
              {canEdit && <button className="primary" onClick={() => setEditing({ kind })}>Add {kind}</button>}
            </div>
            {rows.length === 0 && <p className="empty">No {kind} entries yet.</p>}
            <ul className="rows">
              {rows.map((e) => (
                <EntryRow
                  key={e.id}
                  entry={e}
                  categoryName={e.category_id === null || e.category_id === undefined ? 'Uncategorized' : (names.get(e.category_id) ?? 'Uncategorized')}
                  canEdit={canEdit}
                  onEdit={() => setEditing({ kind, entry: e })}
                  onDelete={() => onDelete(e)}
                />
              ))}
            </ul>
            {editing?.kind === kind && (
              <EntryForm
                key={editing.entry?.id ?? 'new'}
                budgetId={budget.id}
                kind={kind}
                categories={categories.data ?? []}
                entry={editing.entry}
                onDone={done}
                onCancel={() => setEditing(null)}
              />
            )}
          </section>
        )
      })}
      {remove.error && <p className="alert" role="alert">{remove.error}</p>}
    </div>
  )
}
