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
    <main className="auth">
    <form className="card auth-card" onSubmit={onSubmit}>
      <span className="brand">Budget</span>
      <h1>{title}</h1>
      <label className="field">
        Email <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
      </label>
      <label className="field">
        Password <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} required />
      </label>
      {hook.error && <p className="alert" role="alert">{hook.error}</p>}
      <button type="submit" disabled={hook.busy}>{title}</button>
      <p className="auth-alt"><a href={alt.href}>{alt.text}</a></p>
    </form>
    </main>
  )
}
