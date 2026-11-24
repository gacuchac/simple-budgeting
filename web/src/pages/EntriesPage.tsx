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
      {entry.name}: {formatUsd(entry.amount_cents)}, {categoryName}
      {entry.source ? `, from ${entry.source}` : ''}, {describeRule(entry.rule)}
      {canEdit && (
        <>
          {' '}
          <button onClick={onEdit}>Edit</button>
          <button onClick={onDelete}>Delete</button>
        </>
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

  if (entries.loading || categories.loading) return <p>Loading...</p>
  if (entries.error || categories.error) return <p role="alert">{(entries.error ?? categories.error)?.message}</p>

  const names = new Map((categories.data ?? []).map((c) => [c.id, c.name]))
  const done = () => {
    setEditing(null)
    entries.reload()
  }
  const onDelete = async (entry: Entry) => {
    if (window.confirm(`Delete "${entry.name}" and its whole series?`) && (await remove.run(budget.id, entry.id)) !== null) entries.reload()
  }

  return (
    <div>
      {(['income', 'expense'] as const).map((kind) => {
        const rows = (entries.data ?? []).filter((e) => e.kind === kind)
        return (
          <section key={kind}>
            <h2>{kind === 'income' ? 'Income' : 'Expenses'}</h2>
            {rows.length === 0 && <p>No {kind} entries yet.</p>}
            <ul>
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
            {canEdit && <button onClick={() => setEditing({ kind })}>Add {kind}</button>}
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
      {remove.error && <p role="alert">{remove.error}</p>}
    </div>
  )
}
