import { UserPlus } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { acceptInvite, fetchInviteInfo } from '../api'
import { useAuth } from '../auth'
import { Avatar } from '../components/ui'
import type { InviteInfo } from '../types'

// Remember the invite while someone signs up or logs in, so it can be used afterwards
export const PENDING_INVITE_KEY = 'fr_invite'

export default function InvitePage() {
  const { code = '' } = useParams()
  const { user } = useAuth()
  const navigate = useNavigate()
  const [info, setInfo] = useState<InviteInfo | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchInviteInfo(code)
      .then((i) => {
        setInfo(i)
        if (!user) sessionStorage.setItem(PENDING_INVITE_KEY, code)
      })
      .catch((e) => setError((e as Error).message))
  }, [code, user])

  async function accept() {
    try {
      await acceptInvite(code)
      sessionStorage.removeItem(PENDING_INVITE_KEY)
      navigate('/friends')
    } catch (e) {
      setError((e as Error).message)
    }
  }

  const name = info?.inviter.display_name
  const isSelf = !!user && info?.inviter.id === user.id

  return (
    <section className="invite-page card">
      {error && <div className="notice error">{error}</div>}
      {info && (
        <>
          <Avatar name={info.inviter.display_name} size={64} />
          <h1>{isSelf ? 'This is your invite link' : `${name} invited you to Friend Recs`}</h1>
          <p className="hint">
            {isSelf
              ? 'Send it to friends. When they open it, you become friends automatically.'
              : `See ${name}'s favorite places on your map, and share yours.`}
          </p>
          <div className="stack">
            {user && !isSelf && (
              <button className="btn accent" onClick={accept}>
                <UserPlus size={16} /> Add {name} as a friend
              </button>
            )}
            {!user && (
              <>
                <Link to="/register" className="btn accent">Create an account</Link>
                <Link to="/login" className="btn">I already have an account</Link>
              </>
            )}
          </div>
        </>
      )}
    </section>
  )
}
