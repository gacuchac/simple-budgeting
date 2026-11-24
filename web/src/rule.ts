import type { Rule } from './api/client'

export type RuleForm =
  | { shape: 'one_off'; date: string }
  | { shape: 'every'; n: string; unit: 'day' | 'week' | 'month'; start: string; end: string }
  | { shape: 'monthly_on_day'; day: string; start: string; end: string }

const WHOLE = /^\d{1,4}$/

/** Map the rule editor's text fields to the API's `rule` JSON; null when a required field is empty or out of range. */
export function toRule(form: RuleForm): Rule | null {
  switch (form.shape) {
    case 'one_off':
      return form.date ? { type: 'one_off', date: form.date } : null
    case 'every': {
      if (!form.start || !WHOLE.test(form.n) || Number(form.n) < 1) return null
      return { type: 'every', n: Number(form.n), unit: form.unit, start: form.start, end: form.end || null }
    }
    case 'monthly_on_day': {
      const day = Number(form.day)
      if (!form.start || !WHOLE.test(form.day) || day < 1 || day > 31) return null
      return { type: 'monthly_on_day', day, start: form.start, end: form.end || null }
    }
  }
}

/** Fill the rule editor from a stored rule. */
export function fromRule(rule: Rule): RuleForm {
  switch (rule.type) {
    case 'one_off':
      return { shape: 'one_off', date: rule.date }
    case 'every':
      return { shape: 'every', n: String(rule.n), unit: rule.unit, start: rule.start, end: rule.end ?? '' }
    case 'monthly_on_day':
      return { shape: 'monthly_on_day', day: String(rule.day), start: rule.start, end: rule.end ?? '' }
  }
}

/** Describe a rule in one line for the entry lists. */
export function describeRule(rule: Rule): string {
  switch (rule.type) {
    case 'one_off':
      return `once on ${rule.date}`
    case 'every':
      return `every ${rule.n} ${rule.unit}${rule.n === 1 ? '' : 's'} from ${rule.start}${rule.end ? ` to ${rule.end}` : ''}`
    case 'monthly_on_day':
      return `monthly on day ${rule.day} from ${rule.start}${rule.end ? ` to ${rule.end}` : ''}`
  }
}
