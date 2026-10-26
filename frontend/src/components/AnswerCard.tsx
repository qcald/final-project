import { CircleAlert, ShieldCheck } from 'lucide-react'
import { categoryColor } from '../catalog'
import type { AskResponse } from '../types'
import SaveButton from './SaveButton'
import { Avatar, CategoryTag, Rating } from './ui'

export default function AnswerCard({ answer, saved, onSavedChange }: {
  answer: AskResponse
  saved: Set<string>
  onSavedChange: (placeId: string, saved: boolean) => void
}) {
  return (
    <div className="card answer-card">
      <p className="eyebrow">Your friends say</p>
      <p className="answer-summary">{answer.summary}</p>
      {answer.picks.map(({ why, place }, i) => (
        <div key={place.id} className="pick">
          <span className="pick-num" style={{ background: categoryColor(place.category) }}>
            {i + 1}
          </span>
          <div>
            <div className="pick-head">
              <span className="pick-name">{place.name}</span>
              <CategoryTag category={place.category} />
              <span className="hint" style={{ flex: 1 }}>{place.city}</span>
              <SaveButton key={`${place.id}-${saved.has(place.id)}`} placeId={place.id} saved={saved.has(place.id)}
                          onChange={(on) => onSavedChange(place.id, on)} />
            </div>
            <p className="pick-why">{why}</p>
            {place.recs.map((r, j) => (
              <div key={j} className="quote">
                <Avatar name={r.friend} size={26} />
                <div className="quote-bubble">
                  <b>{r.friend}</b>
                  <Rating sentiment={r.sentiment} />
                  <div style={{ marginTop: 4 }}>“{r.quote}”</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ))}
      {answer.not_covered && (
        <div className="notice warn">
          <CircleAlert size={16} />
          <span>
            <b>Not covered by your friends:</b> {answer.not_covered}
          </span>
        </div>
      )}
      {answer.removed_sentences.length > 0 && (
        <div className="notice error">
          <ShieldCheck size={16} />
          <span>
            Removed {answer.removed_sentences.length} sentence(s) that mentioned places no friend recommended:
            <ul>
              {answer.removed_sentences.map((s) => (
                <li key={s}>{s}</li>
              ))}
            </ul>
          </span>
        </div>
      )}
      {answer.blocked > 0 && (
        <div className="notice error">
          <ShieldCheck size={16} />
          <span>
            Blocked {answer.blocked} suggestion(s) that weren't in your friends' recommendations.
          </span>
        </div>
      )}
    </div>
  )
}
