import { useEffect, useState } from 'react'
import { useSignOut } from '../hooks/useAuth'

export function SignOutPage() {
  const signOut = useSignOut()
  const [failed, setFailed] = useState(false)
  useEffect(() => {
    signOut().then(
      () => window.location.assign('/signin'),
      () => setFailed(true),
    )
  }, [])
  if (failed) {
    return (
      <p>
        Sign-out failed, so you are still signed in. <a href="/signout">Try again</a>
      </p>
    )
  }
  return <p>Signing out...</p>
}
