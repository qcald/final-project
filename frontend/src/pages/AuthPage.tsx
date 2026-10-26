import { UserPlus } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth'
import { PENDING_INVITE_KEY } from './InvitePage'
import { Avatar, CategoryTile, Rating } from '../components/ui'
import type { Sentiment } from '../types'

// Example recs for the welcome panel
const HERO_RECS: { name: string; place: string; category: string; sentiment: Sentiment; note: string }[] = [
  { name: 'Jordan', place: 'Manteigaria, Lisbon', category: 'food', sentiment: 'love', note: 'Way better than the famous Belém one.' },
  { name: 'Priya', place: 'Senhora do Monte', category: 'sight', sentiment: 'like', note: 'Go at sunset and bring wine.' },
  { name: 'Dana', place: 'Contramar, CDMX', category: 'food', sentiment: 'love', note: 'Best thing I ate all trip. Book ahead.' },
]

/** Log in and create-account share one form; `mode` picks which. */
export default function AuthPage({ mode }: { mode: 'login' | 'register' }) {
  const { login, register } = useAuth()
  const navigate = useNavigate()
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [displayName, setDisplayName] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)
  const isLogin = mode === 'login'
  const invite = sessionStorage.getItem(PENDING_INVITE_KEY) ?? ''

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      if (isLogin) {
        await login(username, password)
        // Existing accounts confirm the invite on the invite page
        navigate(invite ? `/invite/${invite}` : '/', { replace: true })
      } else {
        await register({ username, email, display_name: displayName, password, invite })
        sessionStorage.removeItem(PENDING_INVITE_KEY)
        navigate(invite ? '/friends' : '/', { replace: true })
      }
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="auth-page">
      <div className="auth-hero">
        <p className="eyebrow">Travel recs from people you trust</p>
        <h1>
          Skip the strangers' reviews. Go where your <em>friends</em> went.
        </h1>
        <p>
          Share the places you love, see your friends' picks on one map, and get a trip plan built only
          from recommendations you actually trust.
        </p>
        <div className="hero-cards">
          {HERO_RECS.map((r) => (
            <div key={r.name} className="hero-card">
              <Avatar name={r.name} size={38} />
              <div style={{ flex: 1 }}>
                <b>{r.name}</b> <Rating sentiment={r.sentiment} />
                <p>
                  <strong>{r.place}</strong> · {r.note}
                </p>
              </div>
              <CategoryTile category={r.category} size={36} />
            </div>
          ))}
        </div>
      </div>

      <div className="auth-side">
        <div className="auth-card">
          <h2>{isLogin ? 'Welcome back' : 'Create your account'}</h2>
          <p className="hint">
            {isLogin ? 'Log in to see what your friends recommend.' : 'It takes ten seconds.'}
          </p>
          {invite && (
            <div className="invite-banner">
              <UserPlus size={16} />
              {isLogin ? 'Log in to accept your friend invite.' : "You'll be friends with whoever invited you as soon as you sign up."}
            </div>
          )}
          <form onSubmit={handleSubmit} className="auth-form" noValidate>
            <label className="field-label" htmlFor="username">{isLogin ? 'Username or email' : 'Username'}</label>
            <input id="username" className="input" value={username} onChange={(e) => setUsername(e.target.value)}
                   autoComplete="username" autoCapitalize="none" required />
            {!isLogin && (
              <>
                <label className="field-label" htmlFor="email">Email</label>
                <input id="email" className="input" type="email" value={email}
                       onChange={(e) => setEmail(e.target.value)} autoComplete="email" required />
                <label className="field-label" htmlFor="display-name">Your name</label>
                <input id="display-name" className="input" value={displayName}
                       onChange={(e) => setDisplayName(e.target.value)} autoComplete="given-name" required />
              </>
            )}
            <label className="field-label" htmlFor="password">Password</label>
            <input id="password" className="input" type="password" value={password}
                   onChange={(e) => setPassword(e.target.value)}
                   autoComplete={isLogin ? 'current-password' : 'new-password'} required />
            {error && <div className="notice error">{error}</div>}
            <button type="submit" className="btn accent" disabled={submitting}>
              {submitting && <span className="spinner" />}
              {isLogin ? 'Log in' : 'Create account'}
            </button>
          </form>
          <p className="auth-switch">
            {isLogin ? (
              <>New here? <Link to="/register">Create an account</Link></>
            ) : (
              <>Already have an account? <Link to="/login">Log in</Link></>
            )}
          </p>
          {isLogin && (
            <div className="demo-hint">
              <b>Trying the demo?</b> Log in as <code>maya</code> with password <code>friendrecs</code>.
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
