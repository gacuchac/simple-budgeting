import { useCallback } from 'react'
import { api, type Category } from '../api/client'
import { useLoaded, type Loaded } from './useAsync'

export function useCategories(budgetId: number): Loaded<Category[]> {
  return useLoaded(useCallback(() => api.categories(budgetId), [budgetId]))
}
