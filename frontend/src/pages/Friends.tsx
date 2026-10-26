import { Check, CircleAlert, CircleCheck, Copy, Link2, UserPlus, Users } from 'lucide-react'
import { useCallback, useEffect, useState, type FormEvent, type ReactNode } from 'react'
import { acceptFriendRequest, fetchFriends, fetchMyInvite, sendFriendRequest } from '../api'
import { Avatar } from '../components/ui'
import type { FriendsResponse, User } from '../types'

function Person({ user, children }: { user: User; children?: ReactNode }) {
  return (
    <div className="person">
      <Avatar name={user.display_name} size={42} />
      <div className="person-name">
        <b>{user.display_name}</b>
        <span className="hint">@{user.username}</span>
      </div>
      {children}
    </div>
  )
}

export default function Friends() {
  const [data, setData] = useState<FriendsResponse | null>(null)
  const [username, setUsername] = useState('')
  const [message, setMessage] = useState<{ kind: 'ok' | 'error'; text: string } | null>(null)
  const [inviteLink, setInviteLink] = useState('')
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    fetchMyInvite()
      .then((i) => setInviteLink(`${window.location.origin}/invite/${i.code}`))
      .catch(() => setInviteLink(''))
  }, [])

  async function copyInvite() {
    await navigator.clipboard.writeText(inviteLink)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const refresh = useCallback(() => {
    fetchFriends()
      .then(setData)
      .catch((e) => setMessage({ kind: 'error', text: (e as Error).message }))
  }, [])

  useEffect(refresh, [refresh])

  async function add(e: FormEvent) {
    e.preventDefault()
    if (!username.trim()) return
    try {
      const res = await sendFriendRequest(username)
      setMessage({
        kind: 'ok',
        text: res.status === 'accepted' ? 'They had already asked you, so you are now friends.' : 'Request sent.',
      })
      setUsername('')
      refresh()
    } catch (err) {
      setMessage({ kind: 'error', text: (err as Error).message })
    }
  }

  async function accept(user: User) {
    try {
      await acceptFriendRequest(user.username)
      setMessage({ kind: 'ok', text: `You and ${user.display_name} are now friends. Their recs are on your map.` })
      refresh()
    } catch (err) {
      setMessage({ kind: 'error', text: (err as Error).message })
    }
  }

  return (
    <div className="page narrow">
      <header className="page-header">
        <p className="eyebrow">Friends</p>
        <h1>Your people</h1>
        <p>Friends see each other's posts. Recs you import from chats stay private.</p>
      </header>

      <div className="stack">
        <form className="card" onSubmit={add}>
          <h3 className="card-title">
            <UserPlus size={16} /> Add a friend
          </h3>
          <p className="card-sub">Ask them for their username, then send a request.</p>
          <div className="inline-form">
            <input className="input" placeholder="@username" value={username}
                   onChange={(e) => setUsername(e.target.value)} autoCapitalize="none" />
            <button className="btn" type="submit">Send request</button>
          </div>
          {message && (
            <div className={`notice ${message.kind}`}>
              {message.kind === 'ok' ? <CircleCheck size={16} /> : <CircleAlert size={16} />}
              <span>{message.text}</span>
            </div>
          )}
        </form>

        {inviteLink && (
          <div className="card">
            <h3 className="card-title">
              <Link2 size={16} /> Invite friends
            </h3>
            <p className="card-sub">Anyone who signs up or logs in with your link becomes your friend.</p>
            <div className="invite-row">
              <input className="input" value={inviteLink} readOnly onFocus={(e) => e.target.select()} />
              <button className="btn" onClick={copyInvite}>
                {copied ? <Check size={15} /> : <Copy size={15} />} {copied ? 'Copied' : 'Copy link'}
              </button>
            </div>
          </div>
        )}

        {data && data.incoming.length > 0 && (
          <div className="card request-card">
            <h3 className="card-title">
              Requests for you <span className="section-count">{data.incoming.length}</span>
            </h3>
            {data.incoming.map((u) => (
              <Person key={u.id} user={u}>
                <button className="btn accent btn-small" onClick={() => accept(u)}>
                  <Check size={14} /> Accept
                </button>
              </Person>
            ))}
          </div>
        )}

        <div className="card">
          <h3 className="card-title">
            <Users size={16} /> Your friends {data && <span className="section-count">{data.friends.length}</span>}
          </h3>
          {data?.friends.length === 0 && <p className="hint">No friends yet. Add someone by username.</p>}
          {data?.friends.map((u) => <Person key={u.id} user={u} />)}
          {data?.outgoing.map((u) => (
            <Person key={u.id} user={u}>
              <span className="rating-badge sentiment-avoid">Request sent</span>
            </Person>
          ))}
        </div>
      </div>
    </div>
  )
}
