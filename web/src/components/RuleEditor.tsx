import { type RuleForm } from '../rule'

const UNITS = ['day', 'week', 'month'] as const

function blank(shape: RuleForm['shape'], date: string): RuleForm {
  switch (shape) {
    case 'one_off':
      return { shape, date }
    case 'every':
      return { shape, n: '1', unit: 'month', start: date, end: '' }
    case 'monthly_on_day':
      return { shape, day: String(Number(date.slice(8)) || 1), start: date, end: '' }
  }
}

export function RuleEditor({ value, onChange, shapes, today }: {
  value: RuleForm
  onChange: (next: RuleForm) => void
  shapes: 'all' | 'one_off' | 'recurring'
  today: string
}) {
  return (
    <fieldset>
      <legend>Repeats</legend>
      <select aria-label="Rule" value={value.shape} onChange={(e) => onChange(blank(e.target.value as RuleForm['shape'], today))}>
        {shapes !== 'recurring' && <option value="one_off">One-off</option>}
        {shapes !== 'one_off' && <option value="every">Every N days, weeks or months</option>}
        {shapes !== 'one_off' && <option value="monthly_on_day">Monthly on a day</option>}
      </select>
      {value.shape === 'one_off' && (
        <label>Date <input type="date" value={value.date} onChange={(e) => onChange({ ...value, date: e.target.value })} required /></label>
      )}
      {value.shape === 'every' && (
        <>
          <label>Every <input type="number" min={1} value={value.n} onChange={(e) => onChange({ ...value, n: e.target.value })} required /></label>
          <select aria-label="Unit" value={value.unit} onChange={(e) => onChange({ ...value, unit: e.target.value as (typeof UNITS)[number] })}>
            {UNITS.map((u) => <option key={u} value={u}>{u}s</option>)}
          </select>
        </>
      )}
      {value.shape === 'monthly_on_day' && (
        <label>Day of month <input type="number" min={1} max={31} value={value.day} onChange={(e) => onChange({ ...value, day: e.target.value })} required /></label>
      )}
      {value.shape !== 'one_off' && (
        <>
          <label>Start <input type="date" value={value.start} onChange={(e) => onChange({ ...value, start: e.target.value })} required /></label>
          <label>End (optional) <input type="date" value={value.end} onChange={(e) => onChange({ ...value, end: e.target.value })} /></label>
        </>
      )}
    </fieldset>
  )
}
