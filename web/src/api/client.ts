import type { components } from './schema'

export type Account = components['schemas']['AccountOut']
export type Budget = components['schemas']['BudgetOut']
export type Credentials = components['schemas']['Credentials']
export type Category = components['schemas']['CategoryOut']
export type CategoryIn = components['schemas']['CategoryIn']
export type Entry = components['schemas']['EntryOut']
export type EntryIn = components['schemas']['EntryIn']
export type EntryChanges = components['schemas']['EntryChanges']
export type Rule = EntryIn['rule']
export type SplitResult = components['schemas']['SplitOut']
export type Dashboard = components['schemas']['DashboardOut']
export type Limit = components['schemas']['LimitOut']
export type LimitIn = components['schemas']['LimitIn']
export type LimitStatus = components['schemas']['LimitStatusOut']
export type LimitCheck = { categoryId: number; date: string; amountCents: number; excludeEntryId?: number }
export type PeriodUnit = 'day' | 'week' | 'month' | 'year'
export type DashboardPeriod = { last: number; unit: PeriodUnit } | { start: string; end: string }

export const SIGN_IN_PATH = '/signin'

export class ApiError extends Error {
  readonly status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

function detailMessage(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown } | null)?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((d) => (typeof d === 'string' ? d : (d as { msg?: string }).msg ?? '')).join('; ')
  return `request failed (${status})`
}

async function request<T>(method: string, path: string, body?: unknown, redirectOn401 = true): Promise<T> {
  const response = await fetch(path, {
    method,
    credentials: 'same-origin',
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (response.status === 401 && redirectOn401) {
    window.location.assign(SIGN_IN_PATH)
  }
  if (!response.ok) {
    const parsed: unknown = await response.json().catch(() => null)
    throw new ApiError(response.status, detailMessage(parsed, response.status))
  }
  return response.status === 204 ? (undefined as T) : ((await response.json()) as T)
}

function periodQuery(period: DashboardPeriod): string {
  const params: Record<string, string> = 'last' in period ? { last: String(period.last), unit: period.unit } : { start: period.start, end: period.end }
  return new URLSearchParams(params).toString()
}

const entriesPath = (budgetId: number) => `/api/budgets/${budgetId}/entries`
const categoriesPath = (budgetId: number) => `/api/budgets/${budgetId}/categories`

const limitsPath = (budgetId: number) => `/api/budgets/${budgetId}/limits`

export const api = {
  me: () => request<Account>('GET', '/api/me'),
  budgets: () => request<Budget[]>('GET', '/api/budgets'),
  signUp: (credentials: Credentials) => request<Account>('POST', '/api/signup', credentials, false),
  signIn: (credentials: Credentials) => request<Account>('POST', '/api/signin', credentials, false),
  signOut: () => request<void>('POST', '/api/signout'),
  categories: (budgetId: number) => request<Category[]>('GET', categoriesPath(budgetId)),
  addCategory: (budgetId: number, body: CategoryIn) => request<Category>('POST', categoriesPath(budgetId), body),
  renameCategory: (budgetId: number, id: number, name: string) =>
    request<Category>('PUT', `${categoriesPath(budgetId)}/${id}`, { name }),
  deleteCategory: (budgetId: number, id: number) => request<void>('DELETE', `${categoriesPath(budgetId)}/${id}`),
  entries: (budgetId: number) => request<Entry[]>('GET', entriesPath(budgetId)),
  addEntry: (budgetId: number, body: EntryIn) => request<Entry>('POST', entriesPath(budgetId), body),
  replaceEntry: (budgetId: number, id: number, body: EntryIn) =>
    request<Entry>('PUT', `${entriesPath(budgetId)}/${id}`, body),
  deleteEntry: (budgetId: number, id: number) => request<void>('DELETE', `${entriesPath(budgetId)}/${id}`),
  splitEntry: (budgetId: number, id: number, at: string, changes: EntryChanges) =>
    request<SplitResult>('POST', `${entriesPath(budgetId)}/${id}/split`, { at, changes }),
  limits: (budgetId: number) => request<Limit[]>('GET', limitsPath(budgetId)),
  setLimit: (budgetId: number, body: LimitIn) => request<Limit>('PUT', limitsPath(budgetId), body),
  deleteLimit: (budgetId: number, id: number) => request<void>('DELETE', `${limitsPath(budgetId)}/${id}`),
  checkLimit: async (budgetId: number, check: LimitCheck): Promise<LimitStatus | null> => {
    const params = new URLSearchParams({ category_id: String(check.categoryId), date: check.date, amount_cents: String(check.amountCents) })
    if (check.excludeEntryId !== undefined) params.set('exclude_entry_id', String(check.excludeEntryId))
    const result = await request<components['schemas']['LimitCheckOut']>('GET', `${limitsPath(budgetId)}/check?${params}`)
    return result.status
  },
  dashboard: (budgetId: number, period: DashboardPeriod) =>
    request<Dashboard>('GET', `/api/budgets/${budgetId}/dashboard?${periodQuery(period)}`),
}
