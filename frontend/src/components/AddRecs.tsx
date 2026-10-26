import { ChevronDown, CircleAlert, CircleCheck, ClipboardPaste, FileUp, MessageCircle, ShieldAlert, ShieldCheck } from 'lucide-react'
import { useState, type ChangeEvent } from 'react'
import { addRecs, importGoogleMaps } from '../api'
import TraceCard from './TraceCard'
import type { AddRecsResponse } from '../types'

export default function AddRecs({ onAdded }: { onAdded: (res: AddRecsResponse) => void }) {
  const [mode, setMode] = useState<'chat' | 'maps'>('chat')
  const [friend, setFriend] = useState('')
  const [city, setCity] = useState('')
  const [text, setText] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<AddRecsResponse | null>(null)
  const [error, setError] = useState('')

  async function submit() {
    if (!text.trim()) return setError(mode === 'chat' ? 'Paste some recommendations first.' : 'Choose or paste a list first.')
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const res = mode === 'chat' ? await addRecs(text, friend) : await importGoogleMaps(text, friend, city)
      setResult(res)
      setText('')
      onAdded(res)
    } catch (e) {
      setError((e as Error).message)
    } finally {
      setLoading(false)
    }
  }

  function readFile(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) file.text().then(setText)
  }

  function switchMode(next: 'chat' | 'maps') {
    setMode(next)
    setText('')
    setResult(null)
    setError('')
  }

  return (
    <details className="card">
      <summary>
        <h3 className="card-title">
          <ClipboardPaste size={16} /> Import recommendations
        </h3>
        <ChevronDown size={18} className="chev" />
      </summary>
      <div className="seg">
        <button type="button" className={mode === 'chat' ? 'active' : ''} onClick={() => switchMode('chat')}>
          <MessageCircle size={14} /> Group chat
        </button>
        <button type="button" className={mode === 'maps' ? 'active' : ''} onClick={() => switchMode('maps')}>
          <FileUp size={14} /> Google Maps list
        </button>
      </div>
      {mode === 'chat' ? (
        <>
          <p className="card-sub">
            Paste a chat, a note, or a text. The Intake agent pulls out each place. Imported recs stay
            private to you.
          </p>
          <input
            className="input"
            placeholder="Friend's name (if it's one person's note)"
            value={friend}
            onChange={(e) => setFriend(e.target.value)}
          />
          <textarea
            className="textarea"
            placeholder="Jordan: you HAVE to get pastéis at Manteigaria..."
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </>
      ) : (
        <>
          <p className="card-sub">
            Export a saved list from Google Takeout (Saved › your list.csv) and upload it here. Imported
            recs stay private to you.
          </p>
          <input className="input" placeholder="Whose list? (leave blank if it's yours)" value={friend}
                 onChange={(e) => setFriend(e.target.value)} />
          <input className="input" placeholder="City the list is for (helps find each place)" value={city}
                 onChange={(e) => setCity(e.target.value)} />
          <label className="file-drop">
            <FileUp size={16} /> {text ? 'File loaded. Choose another?' : 'Choose a .csv file'}
            <input type="file" accept=".csv,text/csv" onChange={readFile} />
          </label>
          <textarea
            className="textarea short"
            placeholder={'…or paste it: Title,Note,URL,Comment'}
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
        </>
      )}
      <button className="btn" onClick={submit} disabled={loading}>
        {loading && <span className="spinner" />}
        {loading ? 'Reading recommendations…' : 'Add to my map'}
      </button>

      {error && (
        <div className="notice error">
          <CircleAlert size={16} /> <span>{error}</span>
        </div>
      )}
      {result && (
        <>
          <div className="notice ok">
            <CircleCheck size={16} />
            <span>
              Found {result.found} recommendations: {result.added} new places, {result.merged} added to
              places already on your map.
              {result.skipped_rows > 0 && ` The list was long, so the last ${result.skipped_rows} places were skipped.`}
            </span>
          </div>
          {result.unverified > 0 && (
            <div className="notice warn">
              <CircleAlert size={16} />
              <span>
                {result.unverified} place(s) couldn't be found on the map. They're saved but marked
                unverified.
              </span>
            </div>
          )}
          {result.pii_removed > 0 && (
            <div className="notice info">
              <ShieldCheck size={16} />
              <span>
                Removed {result.pii_removed} phone number(s) or email(s) before sending the text to the
                model.
              </span>
            </div>
          )}
          {result.ignored_lines.length > 0 && (
            <div className="notice error">
              <ShieldAlert size={16} />
              <span>
                Ignored text that tried to give the AI instructions:
                <ul>
                  {result.ignored_lines.map((line) => (
                    <li key={line}>{line}</li>
                  ))}
                </ul>
              </span>
            </div>
          )}
          <div style={{ marginTop: 12 }}>
            <TraceCard trace={result.trace} title="How this import was made" />
          </div>
        </>
      )}
    </details>
  )
}
