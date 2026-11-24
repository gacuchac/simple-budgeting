import { BudgetProvider, useBudget } from '../hooks/useBudget'
import { useBudgets } from '../hooks/useBudgets'
import { useMe } from '../hooks/useMe'
import { CategoriesPage } from './CategoriesPage'
import { DashboardPage } from './DashboardPage'
import { EntriesPage } from './EntriesPage'

const LINKS = [
  { href: '/', label: 'Dashboard' },
  { href: '/entries', label: 'Entries' },
  { href: '/categories', label: 'Categories' },
]

function Page() {
  switch (window.location.pathname) {
    case '/entries':
      return <EntriesPage />
    case '/categories':
      return <CategoriesPage />
    default:
      return <DashboardPage />
  }
}

function Header({ budgets, email }: { budgets: ReturnType<typeof useBudgets>['data']; email?: string }) {
  const { budget, select } = useBudget()
  return (
    <header>
      <select aria-label="Budget" value={budget.id} onChange={(e) => select(Number(e.target.value))}>
        {(budgets ?? []).map((b) => (
          <option key={b.id} value={b.id}>
            {b.name} ({b.kind}, {b.role})
          </option>
        ))}
      </select>
      <nav>
        {LINKS.map((l) => (
          <a key={l.href} href={l.href} aria-current={window.location.pathname === l.href ? 'page' : undefined}>{l.label} </a>
        ))}
      </nav>
      <span> {email} </span>
      <a href="/signout">Sign out</a>
    </header>
  )
}

export function Shell() {
  const me = useMe()
  const budgets = useBudgets()

  if (me.loading || budgets.loading) return <p>Loading...</p>
  if (me.error || budgets.error) return <p role="alert">{(me.error ?? budgets.error)?.message}</p>
  if (!budgets.data?.length) return <p>No budgets yet.</p>

  return (
    <BudgetProvider budgets={budgets.data}>
      <Header budgets={budgets.data} email={me.data?.email} />
      <main>
        <Page />
      </main>
    </BudgetProvider>
  )
}
