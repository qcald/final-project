import { CircleAlert, Heart, MapPin, Meh, Send, ThumbsDown, ThumbsUp, type LucideIcon } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { createPost } from '../api'
import { RATING_BADGE, categoryColor, categoryIcon } from '../catalog'
import { CATEGORIES, type Category, type FeedItem, type Sentiment } from '../types'

const RATINGS: { value: Sentiment; Icon: LucideIcon }[] = [
  { value: 'love', Icon: Heart },
  { value: 'like', Icon: ThumbsUp },
  { value: 'mixed', Icon: Meh },
  { value: 'avoid', Icon: ThumbsDown },
]

export default function PostForm({ onPosted }: { onPosted: (post: FeedItem) => void }) {
  const [place, setPlace] = useState('')
  const [city, setCity] = useState('')
  const [category, setCategory] = useState<Category>('food')
  const [sentiment, setSentiment] = useState<Sentiment>('love')
  const [note, setNote] = useState('')
  const [posting, setPosting] = useState(false)
  const [error, setError] = useState('')
  const [warning, setWarning] = useState('')
  const [pinned, setPinned] = useState('')

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!place.trim() || !city.trim() || !note.trim()) return setError('Fill in the place, city, and a note.')
    setPosting(true)
    setError('')
    setWarning('')
    setPinned('')
    try {
      const res = await createPost({ place, city, category, sentiment, note })
      if (!res.verified) setWarning(`Posted, but we couldn't find "${place}" on the map, so it won't have a pin.`)
      else setPinned(res.address)
      setPlace('')
      setNote('')
      onPosted(res.post)
    } catch (err) {
      setError((err as Error).message)
    } finally {
      setPosting(false)
    }
  }

  return (
    <form className="card" onSubmit={submit}>
      <h3 className="card-title">
        <Send size={16} /> Share a recommendation
      </h3>
      <p className="card-sub">Your friends see it in their feed, on their map, and when they ask for picks.</p>
      <label className="field-label">Where</label>
      <input className="input" placeholder="Place (e.g. Manteigaria)" value={place}
             onChange={(e) => setPlace(e.target.value)} maxLength={120} />
      <input className="input" placeholder="City" value={city} onChange={(e) => setCity(e.target.value)}
             maxLength={80} />
      <label className="field-label">What kind of place</label>
      <div className="chips">
        {CATEGORIES.map((c) => {
          const Icon = categoryIcon(c)
          return (
            <button type="button" key={c} className={`chip cap${category === c ? ' active' : ''}`}
                    style={category === c ? { background: categoryColor(c), borderColor: categoryColor(c) } : undefined}
                    onClick={() => setCategory(c)}>
              <Icon size={13} /> {c}
            </button>
          )
        })}
      </div>
      <label className="field-label">Your take</label>
      <div className="chips" role="radiogroup" aria-label="Your rating">
        {RATINGS.map(({ value, Icon }) => (
          <button type="button" key={value} role="radio" aria-checked={sentiment === value}
                  className={`chip sentiment-${value}${sentiment === value ? ' active' : ''}`}
                  onClick={() => setSentiment(value)}>
            <Icon size={13} /> {RATING_BADGE[value]}
          </button>
        ))}
      </div>
      <textarea className="textarea short" placeholder="What should your friends know? Order the garlic prawns…"
                value={note} onChange={(e) => setNote(e.target.value)} maxLength={280} />
      <button className="btn accent" type="submit" disabled={posting}>
        {posting ? <span className="spinner" /> : <Send size={15} />}
        {posting ? 'Posting…' : 'Post to friends'}
      </button>
      {error && <div className="notice error"><CircleAlert size={16} /> <span>{error}</span></div>}
      {warning && <div className="notice warn"><CircleAlert size={16} /> <span>{warning}</span></div>}
      {pinned && (
        <div className="notice ok">
          <MapPin size={16} />
          <span>
            <b>Posted and pinned at:</b> {pinned}. Wrong spot? Delete the post and add the neighborhood to
            the place name.
          </span>
        </div>
      )}
    </form>
  )
}
