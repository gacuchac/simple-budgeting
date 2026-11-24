import { render } from '@testing-library/react'
import { expect, test } from 'vitest'
import { DonutChart, markAngle, type Donut } from './DonutChart'

const over: Donut = {
  total_cents: 40000,
  slices: [{ category_id: 1, name: 'Rent', amount_cents: 40000 }],
  remaining_cents: 0,
  mark_cents: 10000,
}

test('the mark sits at 360 x mark / total degrees', () => {
  expect(markAngle(10000, 40000)).toBe(90)
  expect(markAngle(0, 40000)).toBe(0)
})

test('the donut draws the red mark only when expenses exceed income', () => {
  const colours = () => '#4e79a7'
  const { container, rerender } = render(<DonutChart donut={over} colours={colours} />)
  expect(container.querySelector('.income-mark')).not.toBeNull()
  rerender(<DonutChart donut={{ ...over, mark_cents: null }} colours={colours} />)
  expect(container.querySelector('.income-mark')).toBeNull()
})
