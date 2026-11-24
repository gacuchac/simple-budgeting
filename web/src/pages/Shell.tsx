import { useEffect, useState } from 'react'
import { useBudgets } from '../hooks/useBudgets'
import { useMe } from '../hooks/useMe'

export function Shell() {
  const me = useMe()
  const budgets = useBudgets()
  const [selected, setSelected] = useState<number | null>(null)
  const list = budgets.data ?? []
  const current = list.find((b) => b.id === selected) ?? list[0]

  useEffect(() => {
    if (current && selected === null) setSelected(current.id)
  }, [current, selected])

  if (me.loading || budgets.loading) return <p>Loading...</p>
  if (me.error || budgets.error) return <p role="alert">{(me.error ?? budgets.error)?.message}</p>

  return (
    <div>
      <header>
        <select aria-label="Budget" value={current?.id} onChange={(e) => setSelected(Number(e.target.value))}>
          {list.map((b) => (
            <option key={b.id} value={b.id}>
              {b.name} ({b.kind}, {b.role})
            </option>
          ))}
        </select>
        <span> {me.data?.email} </span>
        <a href="/signout">Sign out</a>
      </header>
      <main>{current && <p>Working in {current.name} as {current.role}.</p>}</main>
    </div>
  )
}
