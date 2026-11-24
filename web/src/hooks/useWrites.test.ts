import { act, renderHook } from '@testing-library/react'
import { afterEach, expect, test, vi } from 'vitest'
import { useAddCategory } from './useWrites'

afterEach(() => vi.unstubAllGlobals())

test('useAddCategory posts to the budget and returns the created category', async () => {
  const created = { id: 3, budget_id: 7, kind: 'expense', name: 'Food' }
  const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify(created), { status: 201 }))
  vi.stubGlobal('fetch', fetchMock)
  const { result } = renderHook(() => useAddCategory())
  let saved: unknown
  await act(async () => {
    saved = await result.current.run(7, { kind: 'expense', name: 'Food' })
  })
  expect(saved).toEqual(created)
  expect(fetchMock.mock.calls[0][0]).toBe('/api/budgets/7/categories')
  expect(fetchMock.mock.calls[0][1].method).toBe('POST')
})
