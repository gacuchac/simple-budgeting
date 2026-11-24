import { Cell, Pie, PieChart } from 'recharts'
import type { Dashboard } from '../api/client'
import { REMAINING_COLOUR } from '../colours'
import { formatUsd } from '../money'

export type Donut = Dashboard['donut']

export const MARK_WIDTH_DEGREES = 3
const MARK_COLOUR = '#d03b3b'
const SIZE = 280
const RING_INNER = 98
const RING_OUTER = 120
const LABEL_GAP = 14

/** Degrees clockwise from the top where the red mark sits: 360 x mark / total. */
export function markAngle(markCents: number, totalCents: number): number {
  return totalCents > 0 ? (360 * markCents) / totalCents : 0
}

function MarkLabel({ cx = 0, cy = 0, midAngle = 0 }: { cx?: number; cy?: number; midAngle?: number }) {
  const rad = (Math.PI / 180) * midAngle
  const radius = RING_OUTER + 6 + LABEL_GAP
  const anchor = Math.abs(Math.cos(rad)) < 0.3 ? 'middle' : Math.cos(rad) > 0 ? 'start' : 'end'
  return (
    <text x={cx + radius * Math.cos(rad)} y={cy - radius * Math.sin(rad)} textAnchor={anchor} dominantBaseline="central" fill="var(--critical)" fontSize={12} fontWeight={600}>
      Income
    </text>
  )
}

export function DonutChart({ donut, colours }: { donut: Donut; colours: (categoryId: number | null) => string }) {
  const arcs = [
    ...donut.slices.filter((s) => s.amount_cents > 0).map((s) => ({ key: `c${s.category_id}`, name: s.name, cents: s.amount_cents, colour: colours(s.category_id) })),
    ...(donut.remaining_cents > 0 ? [{ key: 'remaining', name: 'Remaining', cents: donut.remaining_cents, colour: REMAINING_COLOUR }] : []),
  ]
  const mark = donut.mark_cents === null ? null : markAngle(donut.mark_cents, donut.total_cents)
  const centre = SIZE / 2
  const spent = donut.slices.reduce((sum, s) => sum + s.amount_cents, 0)
  const income = donut.mark_cents ?? donut.total_cents
  const whole = arcs.reduce((sum, a) => sum + a.cents, 0) || 1
  return (
    <figure className="donut">
      <div className="donut-wrap" style={{ width: SIZE, height: SIZE }}>
        <PieChart width={SIZE} height={SIZE}>
          <Pie data={arcs} dataKey="cents" nameKey="name" cx={centre} cy={centre} innerRadius={RING_INNER} outerRadius={RING_OUTER} startAngle={90} endAngle={-270} isAnimationActive={false} stroke="var(--surface)" strokeWidth={2}>
            {arcs.map((a) => <Cell key={a.key} fill={a.colour} />)}
          </Pie>
          {mark !== null && (
            <Pie
              data={[{ v: 1 }]}
              dataKey="v"
              cx={centre}
              cy={centre}
              innerRadius={RING_INNER - 6}
              outerRadius={RING_OUTER + 6}
              startAngle={90 - mark + MARK_WIDTH_DEGREES / 2}
              endAngle={90 - mark - MARK_WIDTH_DEGREES / 2}
              isAnimationActive={false}
              stroke="none"
              fill={MARK_COLOUR}
              className="income-mark"
              label={MarkLabel}
              labelLine={false}
            />
          )}
        </PieChart>
        <div className="donut-centre">
          <strong>{formatUsd(spent)}</strong>
          <span>of {formatUsd(income)} income</span>
        </div>
      </div>
      <figcaption>
        <ul className="legend">
          {arcs.map((a) => (
            <li key={a.key}>
              <span className="dot" style={{ background: a.colour }} aria-hidden="true" />
              <span className="name">{a.name}</span>
              <span className="amount">{formatUsd(a.cents)}</span>
              <span className="share">{Math.round((a.cents / whole) * 100)}%</span>
            </li>
          ))}
          {mark !== null && (
            <li className="mark-key">
              <span className="mark-dot" aria-hidden="true" />
              <span className="name">Income mark</span>
              <span className="amount">{formatUsd(donut.mark_cents ?? 0)}</span>
              <span className="share" />
            </li>
          )}
        </ul>
      </figcaption>
    </figure>
  )
}
