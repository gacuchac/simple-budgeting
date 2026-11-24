import { Cell, Pie, PieChart } from 'recharts'
import type { Dashboard } from '../api/client'
import { REMAINING_COLOUR } from '../colours'
import { formatUsd } from '../money'

export type Donut = Dashboard['donut']

export const MARK_WIDTH_DEGREES = 3
const MARK_COLOUR = '#d00000'
const SIZE = 320

/** Degrees clockwise from the top where the red mark sits: 360 x mark / total. */
export function markAngle(markCents: number, totalCents: number): number {
  return totalCents > 0 ? (360 * markCents) / totalCents : 0
}

export function DonutChart({ donut, colours }: { donut: Donut; colours: (categoryId: number | null) => string }) {
  const arcs = [
    ...donut.slices.filter((s) => s.amount_cents > 0).map((s) => ({ key: `c${s.category_id}`, name: s.name, cents: s.amount_cents, colour: colours(s.category_id) })),
    ...(donut.remaining_cents > 0 ? [{ key: 'remaining', name: 'Remaining', cents: donut.remaining_cents, colour: REMAINING_COLOUR }] : []),
  ]
  const mark = donut.mark_cents === null ? null : markAngle(donut.mark_cents, donut.total_cents)
  const centre = SIZE / 2
  return (
    <figure>
      <PieChart width={SIZE} height={SIZE}>
        <Pie data={arcs} dataKey="cents" nameKey="name" cx={centre} cy={centre} innerRadius={90} outerRadius={130} startAngle={90} endAngle={-270} isAnimationActive={false} stroke="none">
          {arcs.map((a) => <Cell key={a.key} fill={a.colour} />)}
        </Pie>
        {mark !== null && (
          <Pie
            data={[{ v: 1 }]}
            dataKey="v"
            cx={centre}
            cy={centre}
            innerRadius={84}
            outerRadius={136}
            startAngle={90 - mark + MARK_WIDTH_DEGREES / 2}
            endAngle={90 - mark - MARK_WIDTH_DEGREES / 2}
            isAnimationActive={false}
            stroke="none"
            fill={MARK_COLOUR}
            className="income-mark"
          />
        )}
      </PieChart>
      <figcaption>
        <ul>
          {arcs.map((a) => (
            <li key={a.key}><span style={{ color: a.colour }}>&#9632;</span> {a.name}: {formatUsd(a.cents)}</li>
          ))}
        </ul>
        {mark !== null && <p>Red mark: income of {formatUsd(donut.mark_cents ?? 0)}.</p>}
        <p>Remaining: {formatUsd(donut.remaining_cents)}</p>
      </figcaption>
    </figure>
  )
}
