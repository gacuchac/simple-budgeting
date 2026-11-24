import { useEffect } from 'react'
import { useSignOut } from '../hooks/useAuth'

export function SignOutPage() {
  const signOut = useSignOut()
  useEffect(() => {
    signOut().then(
      () => window.location.assign('/signin'),
      () => window.location.assign('/signin'),
    )
  }, [])
  return <p>Signing out...</p>
}
