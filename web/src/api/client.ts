import type { components } from './schema'

export type Account = components['schemas']['AccountOut']
export type Budget = components['schemas']['BudgetOut']
export type Credentials = components['schemas']['Credentials']

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

export const api = {
  me: () => request<Account>('GET', '/api/me'),
  budgets: () => request<Budget[]>('GET', '/api/budgets'),
  signUp: (credentials: Credentials) => request<Account>('POST', '/api/signup', credentials, false),
  signIn: (credentials: Credentials) => request<Account>('POST', '/api/signin', credentials, false),
  signOut: () => request<void>('POST', '/api/signout'),
}
