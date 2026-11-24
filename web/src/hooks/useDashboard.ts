import { useCallback } from 'react'
import { api, type Dashboard, type DashboardPeriod } from '../api/client'
import { useLoaded, type Loaded } from './useAsync'

export function useDashboard(budgetId: number, period: DashboardPeriod): Loaded<Dashboard> {
  const key = JSON.stringify(period)
  return useLoaded(useCallback(() => api.dashboard(budgetId, JSON.parse(key) as DashboardPeriod), [budgetId, key]))
}
