import { useSignIn } from '../hooks/useAuth'
import { CredentialsForm } from './CredentialsForm'

export function SignInPage() {
  return <CredentialsForm title="Sign in" hook={useSignIn()} alt={{ href: '/signup', text: 'New here? Sign up' }} />
}
