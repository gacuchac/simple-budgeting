import { describe, expect, it } from 'vitest'
import { readFileSync } from 'node:fs'
import { occurrences, stepDays, type Rule } from './occ'

const golden: { id: string; rule: Rule; lo: string; hi: string; want: string[] }[] = JSON.parse(readFileSync(new URL('./golden.json', import.meta.url), 'utf8'))

describe(`C-1 golden table (TZ=${process.env.TZ ?? 'system'})`, () => {
  it('has at least 15 cases', () => expect(golden.length).toBeGreaterThanOrEqual(15))
  for (const g of golden) it(g.id, () => expect(occurrences(g.rule, g.lo, g.hi)).toEqual(g.want))
})

describe(`C-2 DST (TZ=${process.env.TZ ?? 'system'})`, () => {
  it('61 distinct days from 2026-03-01 to 2026-04-30', () => {
    const days = stepDays('2026-03-01', '2026-04-30')
    expect(days.length).toBe(61)
    expect(new Set(days).size).toBe(61)
  })
  it('counter-check: naive Date + 86400000 ms with toISOString', () => {
    const out: string[] = []
    for (let t = new Date('2026-03-01T00:00:00').getTime(); out.length < 61; t += 86400000) out.push(new Date(t).toISOString().slice(0, 10))
    console.log(`naive toISOString (TZ=${process.env.TZ}): distinct=${new Set(out).size} first=${out[0]} last=${out[60]}`)
  })
})
