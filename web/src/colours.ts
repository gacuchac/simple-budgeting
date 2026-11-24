const SLOTS = 8

export const REMAINING_COLOUR = 'var(--remaining)'
export const UNCATEGORIZED_COLOUR = 'var(--cat-other)'
export const INCOME_COLOUR = 'var(--cat-1)'
export const EXPENSE_COLOUR = 'var(--cat-2)'

/** The theme colour for a category: its id picks one of the 8 slots, so it never changes when other categories come or go; null (Uncategorized) is grey. */
export function categoryColour(categoryId: number | null): string {
  return categoryId === null ? UNCATEGORIZED_COLOUR : `var(--cat-${(categoryId % SLOTS) + 1})`
}
