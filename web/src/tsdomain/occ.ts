// C-1: the M1 recurrence in TypeScript with date-fns, on plain 'YYYY-MM-DD' strings (no time zones).
import { addDays, addMonths, differenceInCalendarDays, format, getDaysInMonth, parseISO, setDate, startOfMonth } from 'date-fns'

export type Rule = { start: string; kind: 'interval' | 'dom'; every: number; unit: 'day' | 'week' | 'month'; dom: number; end: string | null }
const iso = (d: Date) => format(d, 'yyyy-MM-dd')
const p = (s: string) => parseISO(s) // local midnight

function monthWithDay(base: Date, k: number, day: number): Date {
  const m = addMonths(startOfMonth(base), k)
  return setDate(m, Math.min(day, getDaysInMonth(m)))
}

export function occurrences(r: Rule, lo: string, hi: string): string[] {
  const stop = r.end && r.end < hi ? r.end : hi
  const out: string[] = []
  if (r.kind === 'dom' || r.unit === 'month') {
    const day = r.kind === 'dom' ? r.dom : p(r.start).getDate()
    const every = r.kind === 'dom' ? 1 : r.every
    for (let k = 0; ; k++) {
      const d = iso(monthWithDay(p(r.start), k * every, day))
      if (d > stop) return out
      if (d >= r.start && d >= lo) out.push(d)
    }
  }
  const step = r.every * (r.unit === 'week' ? 7 : 1)
  const gap = differenceInCalendarDays(p(lo), p(r.start))
  let k = gap > 0 ? Math.ceil(gap / step) : 0
  for (;; k++) {
    const d = iso(addDays(p(r.start), k * step))
    if (d > stop) return out
    out.push(d)
  }
}

export function stepDays(from: string, to: string): string[] {
  const out: string[] = []
  for (let d = p(from); iso(d) <= to; d = addDays(d, 1)) out.push(iso(d))
  return out
}
