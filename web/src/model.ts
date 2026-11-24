// M3 donut model (TS mirror of spikes/domain/donut.py) used by the chart spike.
export type Arc = { key: string; cents: number; color: string }
export type Donut = { kind: 'empty' } | { kind: 'ring'; total: number; arcs: Arc[]; markDeg: number | null }

const COLORS = ['#4e79a7', '#f28e2b', '#59a14f', '#76b7b2', '#edc948', '#b07aa1']

export function donut(income: number, byCat: [string, number][]): Donut {
  const exp = byCat.reduce((s, [, c]) => s + c, 0)
  if (income === 0 && exp === 0) return { kind: 'empty' }
  const arcs: Arc[] = byCat.map(([k, c], i) => ({ key: k, cents: c, color: COLORS[i % COLORS.length] }))
  if (exp <= income) {
    if (income > exp) arcs.push({ key: 'remaining', cents: income - exp, color: '#e0e0e0' })
    return { kind: 'ring', total: income, arcs, markDeg: null }
  }
  return { kind: 'ring', total: exp, arcs, markDeg: (360 * income) / exp }
}

export const CASES: Record<string, [number, [string, number][]]> = {
  over: [300000, [['Housing', 250000], ['Food', 100000], ['Transport', 50000]]], // mark at 270
  under: [500000, [['Housing', 250000], ['Food', 100000]]],
  zero: [0, [['Housing', 250000], ['Food', 150000]]], // mark at 0 (user: "mark goes at income amount")
  empty: [0, []],
}

export function series(n: number) {
  let inc = 0, exp = 0
  return Array.from({ length: n }, (_, i) => {
    inc += i % 14 === 4 ? 150000 : 0
    exp += 3000 + (i % 7) * 500
    return { d: `2026-01-${String(i + 1).padStart(2, '0')}`, income: inc, expenses: exp }
  })
}
