import { useState } from 'react'
import type { DashboardPeriod, PeriodUnit } from '../api/client'

const UNITS: PeriodUnit[] = ['day', 'week', 'month', 'year']

export function PeriodPicker({ value, onChange }: { value: DashboardPeriod; onChange: (next: DashboardPeriod) => void }) {
  const [last, setLast] = useState('last' in value ? String(value.last) : '1')
  const [unit, setUnit] = useState<PeriodUnit>('last' in value ? value.unit : 'month')
  const [start, setStart] = useState('start' in value ? value.start : '')
  const [end, setEnd] = useState('start' in value ? value.end : '')
  const mode = 'last' in value ? 'last' : 'range'

  const applyLast = (n: string, u: PeriodUnit) => {
    setLast(n)
    setUnit(u)
    if (/^[1-9]\d{0,3}$/.test(n)) onChange({ last: Number(n), unit: u })
  }
  const applyRange = (s: string, e: string) => {
    setStart(s)
    setEnd(e)
    if (s && e) onChange({ start: s, end: e })
  }

  return (
    <fieldset>
      <legend>Period</legend>
      <select aria-label="Period type" value={mode} onChange={(e) => (e.target.value === 'last' ? applyLast(last, unit) : applyRange(start, end))}>
        <option value="last">Last N</option>
        <option value="range">Calendar dates</option>
      </select>
      {mode === 'last' ? (
        <>
          <input aria-label="N" type="number" min={1} value={last} onChange={(e) => applyLast(e.target.value, unit)} />
          <select aria-label="Unit" value={unit} onChange={(e) => applyLast(last, e.target.value as PeriodUnit)}>
            {UNITS.map((u) => <option key={u} value={u}>{u}s</option>)}
          </select>
        </>
      ) : (
        <>
          <label>From <input type="date" value={start} onChange={(e) => applyRange(e.target.value, end)} /></label>
          <label>To <input type="date" value={end} onChange={(e) => applyRange(start, e.target.value)} /></label>
        </>
      )}
    </fieldset>
  )
}
