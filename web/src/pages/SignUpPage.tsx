import { useSignUp } from '../hooks/useAuth'
import { CredentialsForm } from './CredentialsForm'

export function SignUpPage() {
  return <CredentialsForm title="Sign up" hook={useSignUp()} alt={{ href: '/signin', text: 'Have an account? Sign in' }} />
}
