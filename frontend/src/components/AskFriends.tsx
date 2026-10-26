import { Sparkles } from 'lucide-react'
import { useState } from 'react'

interface Props {
  cities: string[]
  city: string
  onCityChange: (city: string) => void
  onAsk: (question: string) => void
  loading: boolean
}

// One-click starting points for a question
const SUGGESTIONS = ['A perfect food day', 'Sunset spots', 'A rainy afternoon', 'Hidden gems only']

export default function AskFriends({ cities, city, onCityChange, onAsk, loading }: Props) {
  const [question, setQuestion] = useState('')

  return (
    <div className="card ask-card">
      <h3 className="card-title">
        <Sparkles size={17} /> Ask your friends
      </h3>
      <p className="card-sub">Get a plan built only from places your friends recommended.</p>
      <select className="input" value={city} onChange={(e) => onCityChange(e.target.value)}>
        <option value="">Anywhere</option>
        {cities.map((c) => (
          <option key={c} value={c}>
            {c}
          </option>
        ))}
      </select>
      <textarea
        className="textarea short"
        placeholder="2 days here, I love food and sunsets. What should I do?"
        value={question}
        onChange={(e) => setQuestion(e.target.value)}
      />
      <div className="chips">
        {SUGGESTIONS.map((s) => (
          <button key={s} type="button" className="chip" onClick={() => setQuestion(s)}>
            {s}
          </button>
        ))}
      </div>
      <button className="btn accent" onClick={() => question.trim() && onAsk(question)} disabled={loading}>
        {loading ? <span className="spinner" /> : <Sparkles size={16} />}
        {loading ? 'Asking your friends…' : 'Ask'}
      </button>
    </div>
  )
}
