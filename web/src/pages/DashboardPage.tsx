import { useState } from 'react'
import type { DashboardPeriod } from '../api/client'
import { DonutChart } from '../components/DonutChart'
import { LineChart } from '../components/LineChart'
import { PeriodPicker } from '../components/PeriodPicker'
import { categoryColour } from '../colours'
import { currentMonth } from '../dates'
import { useBudget } from '../hooks/useBudget'
import { useDashboard } from '../hooks/useDashboard'
import { formatUsd } from '../money'

export function DashboardPage() {
  const { budget } = useBudget()
  const [period, setPeriod] = useState<DashboardPeriod>(currentMonth)
  const { data, error, loading } = useDashboard(budget.id, period)

  return (
    <div>
      <PeriodPicker value={period} onChange={setPeriod} />
      {error && <p role="alert">{error.message}</p>}
      {loading && !data && <p>Loading...</p>}
      {data && !error && (
        <>
          <p>{data.range.start} to {data.range.end}: income {formatUsd(data.income_cents)}, expenses {formatUsd(data.expense_cents)}</p>
          {data.income_cents === 0 && data.expense_cents === 0 ? (
            <p>No income or expenses in this period. Add entries on the Entries page.</p>
          ) : (
            <>
              <DonutChart donut={data.donut} colours={categoryColour} />
              <LineChart lines={data.lines} />
            </>
          )}
        </>
      )}
    </div>
  )
}
