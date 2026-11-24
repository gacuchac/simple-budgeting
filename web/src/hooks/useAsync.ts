import { useCallback, useEffect, useState } from 'react'

export type Loaded<T> = { data: T | null; error: Error | null; loading: boolean; reload: () => void }

type State<T> = { source: unknown; data: T | null; error: Error | null }

export function useLoaded<T>(load: () => Promise<T>): Loaded<T> {
  const [state, setState] = useState<State<T>>({ source: null, data: null, error: null })
  const [version, setVersion] = useState(0)
  const reload = useCallback(() => setVersion((v) => v + 1), [])
  useEffect(() => {
    let live = true
    load().then(
      (data) => live && setState({ source: load, data, error: null }),
      (error: Error) => live && setState({ source: load, data: null, error }),
    )
    return () => {
      live = false
    }
  }, [load, version])
  if (state.source !== load) return { data: null, error: null, loading: true, reload }
  return { data: state.data, error: state.error, loading: false, reload }
}
