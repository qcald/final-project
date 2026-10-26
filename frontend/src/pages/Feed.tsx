import { Newspaper, Pencil, Trash2 } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { deletePost, editPost, fetchFeed } from '../api'
import { RATING_BADGE } from '../catalog'
import PostForm from '../components/PostForm'
import SaveButton from '../components/SaveButton'
import { Avatar, CategoryTag, CategoryTile, Rating } from '../components/ui'
import type { FeedItem, Sentiment } from '../types'

const RATINGS: Sentiment[] = ['love', 'like', 'mixed', 'avoid']

/** SQLite gives UTC "YYYY-MM-DD HH:MM:SS"; show it as "3h ago" etc. */
function timeAgo(utc: string): string {
  const mins = Math.max(0, Math.round((Date.now() - new Date(utc.replace(' ', 'T') + 'Z').getTime()) / 60000))
  if (mins < 1) return 'just now'
  if (mins < 60) return `${mins}m ago`
  if (mins < 60 * 24) return `${Math.round(mins / 60)}h ago`
  return `${Math.round(mins / 1440)}d ago`
}

function Post({ item, onChange, onDelete }: {
  item: FeedItem
  onChange: (item: FeedItem) => void
  onDelete: () => void
}) {
  const [editing, setEditing] = useState(false)
  const [note, setNote] = useState(item.quote)
  const [sentiment, setSentiment] = useState<Sentiment>(item.sentiment)
  const [error, setError] = useState('')

  async function save() {
    try {
      onChange(await editPost(item.id, sentiment, note))
      setEditing(false)
      setError('')
    } catch (e) {
      setError((e as Error).message)
    }
  }

  async function remove() {
    if (!window.confirm(`Delete your post about ${item.place.name}?`)) return
    try {
      await deletePost(item.id)
      onDelete()
    } catch (e) {
      setError((e as Error).message)
    }
  }

  return (
    <article className="card post">
      <div className="post-head">
        <Avatar name={item.author.display_name} size={40} />
        <div className="post-head-text">
          <b>{item.author.is_me ? 'You' : item.author.display_name}</b>
          <span className="hint">
            @{item.author.username} · {timeAgo(item.created_at)}
          </span>
        </div>
        <Rating sentiment={item.sentiment} />
      </div>

      {editing ? (
        <div className="edit-box">
          <div className="chips">
            {RATINGS.map((r) => (
              <button key={r} type="button" className={`chip sentiment-${r}${sentiment === r ? ' active' : ''}`}
                      onClick={() => setSentiment(r)}>
                {RATING_BADGE[r]}
              </button>
            ))}
          </div>
          <textarea className="textarea short" value={note} maxLength={280} onChange={(e) => setNote(e.target.value)} />
          <div className="row">
            <button className="btn btn-small" onClick={save} disabled={!note.trim()}>Save changes</button>
            <button className="ghost-btn" onClick={() => setEditing(false)}>Cancel</button>
          </div>
        </div>
      ) : (
        <p className="post-note">{item.quote}</p>
      )}

      <div className="post-place">
        <CategoryTile category={item.place.category} />
        <div style={{ flex: 1 }}>
          <div className="post-place-name">{item.place.name}</div>
          <div className="post-place-meta">
            <CategoryTag category={item.place.category} />
            {item.place.city}
            {item.place.country ? `, ${item.place.country}` : ''}
          </div>
        </div>
        <SaveButton placeId={item.place.id} saved={item.place.saved} />
      </div>

      {item.author.is_me && !editing && (
        <div className="post-footer">
          <span />
          <div className="post-actions">
            <button className="ghost-btn" onClick={() => setEditing(true)}>
              <Pencil size={13} /> Edit
            </button>
            <button className="ghost-btn danger" onClick={remove}>
              <Trash2 size={13} /> Delete
            </button>
          </div>
        </div>
      )}
      {error && <div className="notice error">{error}</div>}
    </article>
  )
}

export default function Feed() {
  const [items, setItems] = useState<FeedItem[] | null>(null)
  const [error, setError] = useState('')

  useEffect(() => {
    fetchFeed()
      .then(setItems)
      .catch((e) => setError((e as Error).message))
  }, [])

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Feed</p>
        <h1>What your friends are loving</h1>
        <p>The latest recommendations from you and your friends.</p>
      </header>
      <div className="main">
        <div className="left sticky">
          <PostForm onPosted={(post) => setItems((prev) => [post, ...(prev ?? []).filter((p) => p.id !== post.id)])} />
        </div>
        <div className="right">
          {error && <div className="notice error">{error}</div>}
          {items?.length === 0 && (
            <div className="card empty">
              <Newspaper size={28} />
              <p className="hint">
                Nothing here yet. Share a recommendation, or <Link to="/friends">add some friends</Link>.
              </p>
            </div>
          )}
          {items?.map((item) => (
            <Post
              key={item.id}
              item={item}
              onChange={(updated) => setItems((prev) => prev!.map((p) => (p.id === updated.id ? updated : p)))}
              onDelete={() => setItems((prev) => prev!.filter((p) => p.id !== item.id))}
            />
          ))}
        </div>
      </div>
    </div>
  )
}
