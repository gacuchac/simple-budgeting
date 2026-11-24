import { useCallback, useEffect, useState } from 'react'

export type Loaded<T> = { data: T | null; error: Error | null; loading: boolean; reload: () => void }

export function useLoaded<T>(load: () => Promise<T>): Loaded<T> {
  const [state, setState] = useState<Omit<Loaded<T>, 'reload'>>({ data: null, error: null, loading: true })
  const [version, setVersion] = useState(0)
  const reload = useCallback(() => setVersion((v) => v + 1), [])
  useEffect(() => {
    let live = true
    load().then(
      (data) => live && setState({ data, error: null, loading: false }),
      (error: Error) => live && setState({ data: null, error, loading: false }),
    )
    return () => {
      live = false
    }
  }, [load, version])
  return { ...state, reload }
}
