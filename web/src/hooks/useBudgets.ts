import { api, type Budget } from '../api/client'
import { useLoaded, type Loaded } from './useAsync'

export function useBudgets(): Loaded<Budget[]> {
  return useLoaded(api.budgets)
}
