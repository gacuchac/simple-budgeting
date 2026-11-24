import { afterEach, expect, test, vi } from 'vitest'
import { api, ApiError, SIGN_IN_PATH } from './client'

function respond(status: number, body: unknown) {
  vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(body), { status })))
}

afterEach(() => vi.unstubAllGlobals())

test('a 401 sends the user to sign-in', async () => {
  const assign = vi.fn()
  vi.stubGlobal('location', { assign })
  respond(401, { detail: 'Not authenticated' })
  await expect(api.me()).rejects.toBeInstanceOf(ApiError)
  expect(assign).toHaveBeenCalledWith(SIGN_IN_PATH)
})

test('a failed sign-in shows its message and does not redirect', async () => {
  const assign = vi.fn()
  vi.stubGlobal('location', { assign })
  respond(401, { detail: 'invalid email or password' })
  await expect(api.signIn({ email: 'a@b.co', password: 'x' })).rejects.toThrow('invalid email or password')
  expect(assign).not.toHaveBeenCalled()
})
