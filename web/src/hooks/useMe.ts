import { api, type Account } from '../api/client'
import { useLoaded, type Loaded } from './useAsync'

export function useMe(): Loaded<Account> {
  return useLoaded(api.me)
}
