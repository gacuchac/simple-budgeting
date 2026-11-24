// @vitest-environment jsdom
import { renderHook, waitFor } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { useLoaded } from './useAsync'

describe('useLoaded', () => {
  it('clears old data when the loader changes and ignores a stale response', async () => {
    const slow = () => new Promise<string>((r) => setTimeout(() => r('old'), 50))
    const fast = () => Promise.resolve('new')
    const { result, rerender } = renderHook(({ load }) => useLoaded(load), { initialProps: { load: slow } })
    rerender({ load: fast })
    expect(result.current.data).toBeNull()
    expect(result.current.loading).toBe(true)
    await waitFor(() => expect(result.current.data).toBe('new'))
    await new Promise((r) => setTimeout(r, 80))
    expect(result.current.data).toBe('new')
  })
})
