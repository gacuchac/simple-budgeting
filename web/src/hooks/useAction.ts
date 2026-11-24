import { useState } from 'react'

export type Action<A extends unknown[], R> = { run: (...args: A) => Promise<R | null>; error: string | null; busy: boolean }

/** Wrap a write call: `run` returns its result, or null after setting `error` when it failed. */
export function useAction<A extends unknown[], R>(call: (...args: A) => Promise<R>): Action<A, R> {
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const run = async (...args: A): Promise<R | null> => {
    setBusy(true)
    setError(null)
    try {
      return await call(...args)
    } catch (e) {
      setError((e as Error).message)
      return null
    } finally {
      setBusy(false)
    }
  }
  return { run, error, busy }
}
