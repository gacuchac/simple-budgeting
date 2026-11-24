import { useState } from 'react'
import { api, type Credentials } from '../api/client'

export type Submit = { submit: (credentials: Credentials) => Promise<boolean>; error: string | null; busy: boolean }

function useSubmit(action: (credentials: Credentials) => Promise<unknown>): Submit {
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const submit = async (credentials: Credentials): Promise<boolean> => {
    setBusy(true)
    setError(null)
    try {
      await action(credentials)
      return true
    } catch (e) {
      setError((e as Error).message)
      return false
    } finally {
      setBusy(false)
    }
  }
  return { submit, error, busy }
}

export const useSignUp = (): Submit => useSubmit(api.signUp)
export const useSignIn = (): Submit => useSubmit(api.signIn)

export function useSignOut(): () => Promise<void> {
  return () => api.signOut()
}
