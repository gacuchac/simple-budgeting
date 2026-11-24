import { expect, test } from 'vitest'
import { toRule } from './rule'

test('a one-off form maps to a one_off rule', () => {
  expect(toRule({ shape: 'one_off', date: '2026-11-24' })).toEqual({ type: 'one_off', date: '2026-11-24' })
})

test('an every form maps n to a number and an empty end to null', () => {
  expect(toRule({ shape: 'every', n: '2', unit: 'week', start: '2026-11-01', end: '' })).toEqual({
    type: 'every', n: 2, unit: 'week', start: '2026-11-01', end: null,
  })
})

test('a monthly form maps the day and keeps an end date', () => {
  expect(toRule({ shape: 'monthly_on_day', day: '31', start: '2026-01-01', end: '2026-12-31' })).toEqual({
    type: 'monthly_on_day', day: 31, start: '2026-01-01', end: '2026-12-31',
  })
  expect(toRule({ shape: 'monthly_on_day', day: '32', start: '2026-01-01', end: '' })).toBeNull()
})
