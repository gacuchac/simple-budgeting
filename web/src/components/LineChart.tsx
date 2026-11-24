import { CartesianGrid, Legend, Line, LineChart as RechartsLine, Tooltip, XAxis, YAxis } from 'recharts'
import type { Dashboard } from '../api/client'
import { formatUsd } from '../money'

export function LineChart({ lines }: { lines: Dashboard['lines'] }) {
  return (
    <RechartsLine width={640} height={280} data={lines.points}>
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis dataKey="date" />
      <YAxis tickFormatter={(v: number) => formatUsd(v)} width={90} />
      <Tooltip formatter={(v) => formatUsd(Number(v))} />
      <Legend />
      <Line type="stepAfter" dataKey="income_cum" name="Income" stroke="#59a14f" dot={false} isAnimationActive={false} />
      <Line type="stepAfter" dataKey="expense_cum" name="Expenses" stroke="#e15759" dot={false} isAnimationActive={false} />
    </RechartsLine>
  )
}
