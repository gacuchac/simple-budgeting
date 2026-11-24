import { useEffect, useState } from 'react'
import { api, type LimitCheck, type LimitStatus } from '../api/client'

const DEBOUNCE_MS = 300

/** The limit status of the category if `check` were saved, or null when `check` is null, the category has no limit, or the request failed. Re-checks (debounced) when the check changes. */
export function useLimitCheck(budgetId: number, check: LimitCheck | null): LimitStatus | null {
  const [result, setResult] = useState<{ key: string; status: LimitStatus | null } | null>(null)
  const key = check === null ? null : JSON.stringify(check)
  useEffect(() => {
    if (key === null) return
    let live = true
    const timer = setTimeout(() => {
      api.checkLimit(budgetId, JSON.parse(key) as LimitCheck).then(
        (status) => live && setResult({ key, status }),
        () => live && setResult({ key, status: null }),
      )
    }, DEBOUNCE_MS)
    return () => {
      live = false
      clearTimeout(timer)
    }
  }, [budgetId, key])
  return key !== null && result?.key === key ? result.status : null
}
