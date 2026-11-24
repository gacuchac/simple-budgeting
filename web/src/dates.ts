function iso(date: Date): string {
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${date.getFullYear()}-${month}-${day}`
}

/** Today's local date as YYYY-MM-DD. */
export function today(now: Date = new Date()): string {
  return iso(now)
}

/** First and last day of the local calendar month containing `now`, as YYYY-MM-DD. */
export function currentMonth(now: Date = new Date()): { start: string; end: string } {
  return {
    start: iso(new Date(now.getFullYear(), now.getMonth(), 1)),
    end: iso(new Date(now.getFullYear(), now.getMonth() + 1, 0)),
  }
}
