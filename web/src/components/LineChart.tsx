import { CartesianGrid, Legend, Line, LineChart as RechartsLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { Dashboard } from '../api/client'
import { EXPENSE_COLOUR, INCOME_COLOUR } from '../colours'
import { formatUsd } from '../money'

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
const AXIS = { fill: 'var(--muted)', fontSize: 12 }

/** Turn an ISO date such as "2026-11-24" into "Nov 24"; anything else comes back unchanged. */
export function shortDate(iso: string): string {
  const match = /^\d{4}-(\d{2})-(\d{2})$/.exec(iso)
  return match ? `${MONTHS[Number(match[1]) - 1]} ${Number(match[2])}` : iso
}

function usdAxis(cents: number): string {
  return `$${Math.round(cents / 100).toLocaleString('en-US')}`
}

type TipProps = { active?: boolean; label?: string | number; payload?: { name?: string | number; value?: unknown; color?: string }[] }

function ChartTooltip({ active, label, payload }: TipProps) {
  if (!active || !payload?.length) return null
  return (
    <div className="chart-tooltip">
      <strong>{shortDate(String(label))}</strong>
      {payload.map((p) => (
        <div className="row" key={String(p.name)}>
          <span><span className="dot" style={{ background: p.color }} />{p.name}</span>
          <span className="num">{formatUsd(Number(p.value))}</span>
        </div>
      ))}
    </div>
  )
}

export function LineChart({ lines }: { lines: Dashboard['lines'] }) {
  return (
    <div className="line-chart">
      <ResponsiveContainer width="100%" height={300}>
        <RechartsLine data={lines.points} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
          <CartesianGrid stroke="var(--line)" strokeWidth={1} vertical={false} />
          <XAxis dataKey="date" tickFormatter={shortDate} tick={AXIS} stroke="var(--line)" tickLine={false} minTickGap={32} />
          <YAxis tickFormatter={usdAxis} tick={AXIS} width={64} axisLine={false} tickLine={false} />
          <Tooltip content={<ChartTooltip />} cursor={{ stroke: 'var(--muted)', strokeWidth: 1 }} />
          <Legend iconType="plainline" wrapperStyle={{ color: 'var(--ink-2)', fontSize: 13 }} />
          <Line type="stepAfter" dataKey="income_cum" name="Income" stroke={INCOME_COLOUR} strokeWidth={2} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} isAnimationActive={false} />
          <Line type="stepAfter" dataKey="expense_cum" name="Expenses" stroke={EXPENSE_COLOUR} strokeWidth={2} dot={false} activeDot={{ r: 4, strokeWidth: 0 }} isAnimationActive={false} />
        </RechartsLine>
      </ResponsiveContainer>
    </div>
  )
}
