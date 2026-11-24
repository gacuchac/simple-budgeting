import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import { api, type Budget, type Category } from '../api/client'
import { BudgetProvider } from '../hooks/useBudget'
import { CategoriesPage } from './CategoriesPage'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

const budget = { id: 1, role: 'editor' } as Budget
const food: Category = { id: 3, budget_id: 1, kind: 'expense', name: 'Food' }

function renderPage() {
  vi.spyOn(api, 'categories').mockResolvedValue([food])
  render(<BudgetProvider budgets={[budget]}><CategoriesPage /></BudgetProvider>)
}

test('no limit editor is shown while limits load', async () => {
  vi.spyOn(api, 'limits').mockReturnValue(new Promise(() => {}))
  renderPage()
  expect(await screen.findByText('Loading limit...')).toBeTruthy()
  expect(screen.queryByLabelText('Limit amount (USD)')).toBeNull()
})

test('a failed limits fetch shows the error and no limit editor', async () => {
  vi.spyOn(api, 'limits').mockRejectedValue(new Error('limits down'))
  renderPage()
  expect((await screen.findByRole('alert')).textContent).toBe('limits down')
  expect(screen.queryByLabelText('Limit amount (USD)')).toBeNull()
})
