import { useCallback } from 'react'
import { api, type Entry } from '../api/client'
import { useLoaded, type Loaded } from './useAsync'

export function useEntries(budgetId: number): Loaded<Entry[]> {
  return useLoaded(useCallback(() => api.entries(budgetId), [budgetId]))
}
