const PALETTE = ['#4e79a7', '#f28e2b', '#76b7b2', '#b07aa1', '#edc948', '#9c755f', '#59a14f', '#ff9da7', '#86bcb6', '#bab0ac']

export const REMAINING_COLOUR = '#e0e0e0'
export const UNCATEGORIZED_COLOUR = '#999999'

/** A colour for a category that depends only on its id, so it never changes between periods; null is uncategorized. */
export function categoryColour(categoryId: number | null): string {
  return categoryId === null ? UNCATEGORIZED_COLOUR : PALETTE[categoryId % PALETTE.length]
}
