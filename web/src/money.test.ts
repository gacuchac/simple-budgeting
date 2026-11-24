import { expect, test } from 'vitest'
import { formatUsd, parseCents } from './money'

test('parseCents turns dollar strings into integer cents', () => {
  expect(parseCents('12')).toBe(1200)
  expect(parseCents('12.5')).toBe(1250)
  expect(parseCents('$1,200.05')).toBe(120005)
  expect(parseCents('0.07')).toBe(7)
})

test('parseCents rejects more than two decimals and non-numbers', () => {
  expect(parseCents('1.234')).toBeNull()
  expect(parseCents('abc')).toBeNull()
  expect(parseCents('-5')).toBeNull()
  expect(parseCents('')).toBeNull()
})

test('formatUsd formats cents as dollars', () => {
  expect(formatUsd(123456)).toBe('$1,234.56')
})
