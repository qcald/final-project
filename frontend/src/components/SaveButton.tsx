import { Bookmark, BookmarkCheck } from 'lucide-react'
import { useState } from 'react'
import { setSaved } from '../api'

/** "Want to go" toggle for a place. Flips right away and rolls back if the request fails. */
export default function SaveButton({ placeId, saved, onChange, compact = false }: {
  placeId: string
  saved: boolean
  onChange?: (saved: boolean) => void
  compact?: boolean
}) {
  const [on, setOn] = useState(saved)

  async function toggle() {
    const next = !on
    setOn(next)
    onChange?.(next)
    try {
      await setSaved(placeId, next)
    } catch {
      setOn(!next)
      onChange?.(!next)
    }
  }

  return (
    <button type="button" className={`save-btn${on ? ' on' : ''}${compact ? ' compact' : ''}`} onClick={toggle}
            aria-pressed={on} title={on ? 'Remove from want to go' : 'Save to want to go'}>
      {on ? <BookmarkCheck size={14} /> : <Bookmark size={14} />}
      {!compact && (on ? 'Saved' : 'Want to go')}
    </button>
  )
}
