import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import { api, type Category, type LimitStatus } from '../api/client'
import { EntryForm } from './EntryForm'
import { OverLimitList } from './OverLimitList'

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

const food: Category = { id: 3, budget_id: 1, kind: 'expense', name: 'Food' }
const status = (spent: number): LimitStatus => ({ limit_id: 9, category_id: 3, allowed_cents: 10000, spent_cents: spent, over: spent > 10000 })

test('the dashboard marker shows only categories that are over', () => {
  const { rerender } = render(<OverLimitList limits={[status(5000)]} categories={[food]} />)
  expect(screen.queryByText('Over limit')).toBeNull()
  rerender(<OverLimitList limits={[status(11000)]} categories={[food]} />)
  expect(screen.getByText('Over limit')).toBeTruthy()
})

test('the expense form warns at $60 on top of $50 spent against a $100 limit, not at $40', async () => {
  const check = vi.spyOn(api, 'checkLimit').mockImplementation(async (_b, c) => status(5000 + c.amountCents))
  render(<EntryForm budgetId={1} kind="expense" categories={[food]} onDone={() => {}} onCancel={() => {}} />)
  fireEvent.change(screen.getByLabelText(/Category/), { target: { value: '3' } })
  fireEvent.change(screen.getByLabelText(/Amount/), { target: { value: '40' } })
  await waitFor(() => expect(check).toHaveBeenCalled())
  expect(screen.queryByText('Over limit')).toBeNull()
  fireEvent.change(screen.getByLabelText(/Amount/), { target: { value: '60' } })
  expect(await screen.findByText('Over limit')).toBeTruthy()
})
