const SLOTS = 8

export const REMAINING_COLOUR = 'var(--remaining)'
export const UNCATEGORIZED_COLOUR = 'var(--cat-other)'
export const INCOME_COLOUR = 'var(--cat-1)'
export const EXPENSE_COLOUR = 'var(--cat-2)'

/** The theme colour for a category's position in the budget's category list: slots 1 to 8, then grey. */
export function slotColour(position: number): string {
  return position >= 0 && position < SLOTS ? `var(--cat-${position + 1})` : UNCATEGORIZED_COLOUR
}

/** A colour lookup that follows each category's stable position in `categories` (pass one kind's list); null, unknown ids and positions beyond 8 are grey. */
export function categoryColours(categories: { id: number }[]): (categoryId: number | null) => string {
  const positions = new Map(categories.map((c, i) => [c.id, i]))
  return (categoryId) => (categoryId === null ? UNCATEGORIZED_COLOUR : slotColour(positions.get(categoryId) ?? -1))
}
