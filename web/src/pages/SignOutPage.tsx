import { useEffect, useRef, useState } from 'react'
import { useSignOut } from '../hooks/useAuth'

export function SignOutPage() {
  const signOut = useSignOut()
  const started = useRef(false)
  const [failed, setFailed] = useState(false)
  useEffect(() => {
    if (started.current) return
    started.current = true
    signOut().then(
      () => window.location.assign('/signin'),
      () => setFailed(true),
    )
  }, [])
  if (failed) {
    return (
      <p className="status-message">
        Sign-out failed, so you are still signed in. <a href="/signout">Try again</a>
      </p>
    )
  }
  return <p className="status-message">Signing out...</p>
}
