import { useCallback } from 'react'
import { api, type Limit } from '../api/client'
import { useLoaded, type Loaded } from './useAsync'

export function useLimits(budgetId: number): Loaded<Limit[]> {
  return useLoaded(useCallback(() => api.limits(budgetId), [budgetId]))
}
