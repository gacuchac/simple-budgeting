import { useState, type FormEvent } from 'react'
import type { Category, Limit } from '../api/client'
import { categoryColour } from '../colours'
import { useBudget } from '../hooks/useBudget'
import { LimitEditor } from '../components/LimitEditor'
import { useCategories } from '../hooks/useCategories'
import type { Loaded } from '../hooks/useAsync'
import { useLimits } from '../hooks/useLimits'
import { useAddCategory, useDeleteCategory, useRenameCategory } from '../hooks/useWrites'

type RowProps = { category: Category; colour: string; canEdit: boolean; onChanged: () => void; budgetId: number; limits: Loaded<Limit[]> }

function RowLimit({ budgetId, categoryId, limits }: { budgetId: number; categoryId: number; limits: Loaded<Limit[]> }) {
  if (limits.loading) return <span className="status-message">Loading limit...</span>
  if (limits.error) return <span className="alert" role="alert">{limits.error.message}</span>
  const limit = limits.data?.find((l) => l.category_id === categoryId)
  return <LimitEditor key={limit ? `${limit.id}-${limit.amount_cents}-${limit.period}` : 'none'} budgetId={budgetId} categoryId={categoryId} limit={limit} onChanged={limits.reload} />
}

function CategoryRow({ category, colour, canEdit, onChanged, budgetId, limits }: RowProps) {
  const rename = useRenameCategory()
  const remove = useDeleteCategory()
  const onRename = async () => {
    const name = window.prompt('New name', category.name)?.trim()
    if (name && name !== category.name && (await rename.run(budgetId, category.id, name)) !== null) onChanged()
  }
  const onDelete = async () => {
    if (window.confirm(`Delete "${category.name}"? Its entries become uncategorized.`) && (await remove.run(budgetId, category.id)) !== null) onChanged()
  }
  return (
    <li className="cat-row">
      <span className="dot" style={{ background: colour }} aria-hidden="true" />
      <span className="row-name">{category.name}</span>
      {canEdit && (
        <>
          <button className="ghost" onClick={onRename}>Rename</button>
          <button className="ghost danger" onClick={onDelete}>Delete</button>
        </>
      )}
      {(rename.error ?? remove.error) && <span className="alert" role="alert">{rename.error ?? remove.error}</span>}
      {canEdit && category.kind === 'expense' && <RowLimit budgetId={budgetId} categoryId={category.id} limits={limits} />}
    </li>
  )
}

function AddCategory({ budgetId, kind, onAdded }: { budgetId: number; kind: Category['kind']; onAdded: () => void }) {
  const [name, setName] = useState('')
  const add = useAddCategory()
  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if ((await add.run(budgetId, { kind, name: name.trim() })) !== null) {
      setName('')
      onAdded()
    }
  }
  return (
    <form className="add-row" onSubmit={onSubmit}>
      <input aria-label={`New ${kind} category`} value={name} onChange={(e) => setName(e.target.value)} required />
      <button type="submit" disabled={add.busy}>Add</button>
      {add.error && <span className="alert" role="alert">{add.error}</span>}
    </form>
  )
}

export function CategoriesPage() {
  const { budget, canEdit } = useBudget()
  const categories = useCategories(budget.id)
  const limits = useLimits(budget.id)
  if (categories.loading) return <p className="status-message">Loading...</p>
  if (categories.error) return <p className="status-message alert" role="alert">{categories.error.message}</p>
  const all = categories.data ?? []
  return (
    <div className="cols">
      {(['income', 'expense'] as const).map((kind) => (
        <section className="card" key={kind}>
          <div className="card-head"><h2>{kind === 'income' ? 'Income categories' : 'Expense categories'}</h2></div>
          <ul className="rows">
            {all.filter((c) => c.kind === kind).map((c) => (
              <CategoryRow key={c.id} category={c} colour={categoryColour(c.id)} canEdit={canEdit} budgetId={budget.id} onChanged={() => { categories.reload(); limits.reload() }} limits={limits} />
            ))}
          </ul>
          {canEdit && <AddCategory budgetId={budget.id} kind={kind} onAdded={categories.reload} />}
        </section>
      ))}
    </div>
  )
}
