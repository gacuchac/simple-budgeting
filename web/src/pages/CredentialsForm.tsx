import { useState, type FormEvent } from 'react'
import type { Submit } from '../hooks/useAuth'

export function CredentialsForm({ title, hook, alt }: { title: string; hook: Submit; alt: { href: string; text: string } }) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  const onSubmit = async (event: FormEvent) => {
    event.preventDefault()
    if (await hook.submit({ email, password })) window.location.assign('/')
  }

  return (
    <form onSubmit={onSubmit}>
      <h1>{title}</h1>
      <label>
        Email <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      </label>
      <label>
        Password <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
      </label>
      {hook.error && <p role="alert">{hook.error}</p>}
      <button type="submit" disabled={hook.busy}>{title}</button>
      <p><a href={alt.href}>{alt.text}</a></p>
    </form>
  )
}
