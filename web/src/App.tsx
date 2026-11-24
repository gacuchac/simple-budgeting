import { Shell } from './pages/Shell'
import { SignInPage } from './pages/SignInPage'
import { SignOutPage } from './pages/SignOutPage'
import { SignUpPage } from './pages/SignUpPage'

export function App() {
  switch (window.location.pathname) {
    case '/signin':
      return <SignInPage />
    case '/signup':
      return <SignUpPage />
    case '/signout':
      return <SignOutPage />
    default:
      return <Shell />
  }
}
