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

function NetTile({ netCents }: { netCents: number }) {
  const over = netCents < 0
  return (
    <div className={`card stat ${over ? 'critical' : 'good'}`}>
      <span className="stat-label">{over ? 'Over by' : 'Net'}</span>
      <span className="stat-value">{formatUsd(Math.abs(netCents))}</span>
      <span className="stat-note">
        <span aria-hidden="true">{over ? '▲' : '✓'}</span>
        {over ? 'Expenses exceed income' : 'Within income'}
      </span>
    </div>
  )
}

export function DashboardPage() {
  const { budget } = useBudget()
  const [period, setPeriod] = useState<DashboardPeriod>(currentMonth)
  const { data, error, loading } = useDashboard(budget.id, period)

  return (
    <>
      <div className="card">
        <PeriodPicker value={period} onChange={setPeriod} />
      </div>
      {error && <p className="alert" role="alert">{error.message}</p>}
      {loading && !data && <p className="status-message">Loading...</p>}
      {data && !error && (
        <>
          <p className="range-text">{data.range.start} to {data.range.end}</p>
          <div className="stats">
            <div className="card stat">
              <span className="stat-label">Income</span>
              <span className="stat-value">{formatUsd(data.income_cents)}</span>
            </div>
            <div className="card stat">
              <span className="stat-label">Expenses</span>
              <span className="stat-value">{formatUsd(data.expense_cents)}</span>
            </div>
            <NetTile netCents={data.income_cents - data.expense_cents} />
          </div>
          {data.income_cents === 0 && data.expense_cents === 0 ? (
            <div className="card empty-card">
              <p>No income or expenses in this period. Add entries on the Entries page.</p>
              <a href="/entries"><button type="button" className="primary">Go to Entries</button></a>
            </div>
          ) : (
            <div className="charts">
              <section className="card">
                <h2 className="chart-title">Expenses by category</h2>
                <DonutChart donut={data.donut} colours={categoryColour} />
              </section>
              <section className="card">
                <h2 className="chart-title">Cumulative income and expenses</h2>
                <LineChart lines={data.lines} />
              </section>
            </div>
          )}
        </>
      )}
    </>
  )
}
