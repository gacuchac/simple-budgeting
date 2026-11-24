import { renderHook, waitFor } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import { useBudgets } from './useBudgets'

afterEach(() => vi.unstubAllGlobals())

test('useBudgets loads the budget list', async () => {
  const budgets = [{ id: 1, name: 'Personal', kind: 'personal', role: 'editor' }]
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(budgets), { status: 200 })))
  const { result } = renderHook(() => useBudgets())
  await waitFor(() => expect(result.current.loading).toBe(false))
  expect(result.current.data).toEqual(budgets)
})
