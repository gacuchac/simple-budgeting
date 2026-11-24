import { useState, type FormEvent } from 'react'
import type { Category } from '../api/client'
import { categoryColours } from '../colours'
import { useBudget } from '../hooks/useBudget'
import { useCategories } from '../hooks/useCategories'
import { useAddCategory, useDeleteCategory, useRenameCategory } from '../hooks/useWrites'

function CategoryRow({ category, colour, canEdit, onChanged, budgetId }: { category: Category; colour: string; canEdit: boolean; onChanged: () => void; budgetId: number }) {
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
  if (categories.loading) return <p className="status-message">Loading...</p>
  if (categories.error) return <p className="status-message alert" role="alert">{categories.error.message}</p>
  const all = categories.data ?? []
  const colourOf = {
    income: categoryColours(all.filter((c) => c.kind === 'income')),
    expense: categoryColours(all.filter((c) => c.kind === 'expense')),
  }
  return (
    <div className="cols">
      {(['income', 'expense'] as const).map((kind) => (
        <section className="card" key={kind}>
          <div className="card-head"><h2>{kind === 'income' ? 'Income categories' : 'Expense categories'}</h2></div>
          <ul className="rows">
            {all.filter((c) => c.kind === kind).map((c) => (
              <CategoryRow key={c.id} category={c} colour={colourOf[kind](c.id)} canEdit={canEdit} budgetId={budget.id} onChanged={categories.reload} />
            ))}
          </ul>
          {canEdit && <AddCategory budgetId={budget.id} kind={kind} onAdded={categories.reload} />}
        </section>
      ))}
    </div>
  )
}
