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
    <header className="topbar">
      <div className="topbar-inner">
      <span className="brand">Budget</span>
      <nav className="nav">
        {LINKS.map((l) => (
          <a key={l.href} href={l.href} aria-current={window.location.pathname === l.href ? 'page' : undefined}>{l.label}</a>
        ))}
      </nav>
      <div className="topbar-end">
      <select aria-label="Budget" value={budget.id} onChange={(e) => select(Number(e.target.value))}>
        {(budgets ?? []).map((b) => (
          <option key={b.id} value={b.id}>
            {b.name} ({b.kind}, {b.role})
          </option>
        ))}
      </select>
      <span className="email">{email}</span>
      <a href="/signout">Sign out</a>
      </div>
      </div>
    </header>
  )
}

export function Shell() {
  const me = useMe()
  const budgets = useBudgets()

  if (me.loading || budgets.loading) return <p className="status-message">Loading...</p>
  if (me.error || budgets.error) return <p className="status-message alert" role="alert">{(me.error ?? budgets.error)?.message}</p>
  if (!budgets.data?.length) return <p className="status-message">No budgets yet.</p>

  return (
    <BudgetProvider budgets={budgets.data}>
      <Header budgets={budgets.data} email={me.data?.email} />
      <main className="page">
        <Page />
      </main>
    </BudgetProvider>
  )
}
