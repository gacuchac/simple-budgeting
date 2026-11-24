import { createContext, useContext, useMemo, useState, type ReactNode } from 'react'
import type { Budget } from '../api/client'

export type SelectedBudget = { budget: Budget; select: (id: number) => void; canEdit: boolean }

const BudgetContext = createContext<SelectedBudget | null>(null)
const STORAGE_KEY = 'budget-app.selected'

/** Hold the switcher's choice for every page below it; `budgets` must not be empty. */
export function BudgetProvider({ budgets, children }: { budgets: Budget[]; children: ReactNode }) {
  const [selected, setSelected] = useState<number | null>(() => Number(sessionStorage.getItem(STORAGE_KEY)) || null)
  const budget = budgets.find((b) => b.id === selected) ?? budgets[0]
  const value = useMemo<SelectedBudget>(
    () => ({
      budget,
      canEdit: budget.role === 'editor',
      select: (id) => {
        sessionStorage.setItem(STORAGE_KEY, String(id))
        setSelected(id)
      },
    }),
    [budget],
  )
  return <BudgetContext.Provider value={value}>{children}</BudgetContext.Provider>
}

/** The budget chosen in the switcher; only valid under BudgetProvider. */
export function useBudget(): SelectedBudget {
  const value = useContext(BudgetContext)
  if (!value) throw new Error('useBudget needs a BudgetProvider')
  return value
}
