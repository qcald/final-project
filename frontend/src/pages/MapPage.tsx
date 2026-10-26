import { Bookmark, Map as MapIcon } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { askFriends, fetchCities, fetchPlaces } from '../api'
import AddRecs from '../components/AddRecs'
import AnswerCard from '../components/AnswerCard'
import AskFriends from '../components/AskFriends'
import PlaceMap from '../components/PlaceMap'
import RunStatsCard from '../components/RunStatsCard'
import TraceCard from '../components/TraceCard'
import type { AskResponse, Place, RunStats } from '../types'

export default function MapPage() {
  const [places, setPlaces] = useState<Place[]>([])
  const [cities, setCities] = useState<string[]>([])
  const [city, setCity] = useState('')
  const [answer, setAnswer] = useState<AskResponse | null>(null)
  const [asking, setAsking] = useState(false)
  const [askError, setAskError] = useState('')
  const [run, setRun] = useState<RunStats | null>(null)
  const [loadError, setLoadError] = useState('')
  const [onlySaved, setOnlySaved] = useState(false)

  const refresh = useCallback(() => {
    Promise.all([fetchPlaces(city), fetchCities()])
      .then(([p, c]) => {
        setPlaces(p)
        setCities(c)
        setLoadError('')
      })
      .catch(() => setLoadError("Can't reach the backend. Is it running on port 8000?"))
  }, [city])

  useEffect(refresh, [refresh])

  async function ask(question: string) {
    setAsking(true)
    setAskError('')
    setAnswer(null)
    try {
      const res = await askFriends(question, city)
      setAnswer(res)
      setRun(res.run)
    } catch (e) {
      setAskError((e as Error).message)
    } finally {
      setAsking(false)
    }
  }

  // Memoized so the map only re-zooms when a new answer arrives
  const picks = useMemo(() => (answer ? answer.picks.map((p) => p.place.id) : []), [answer])
  const savedIds = useMemo(() => new Set(places.filter((p) => p.saved).map((p) => p.id)), [places])
  const shown = useMemo(() => (onlySaved ? places.filter((p) => p.saved) : places), [places, onlySaved])
  const markSaved = (placeId: string, saved: boolean) =>
    setPlaces((prev) => prev.map((p) => (p.id === placeId ? { ...p, saved } : p)))

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Map</p>
        <h1>Where your friends would go</h1>
        <p>Everything you and your friends recommend, plus recs you've pulled out of group chats.</p>
      </header>
      {loadError && <div className="notice error" style={{ marginBottom: 20 }}>{loadError}</div>}

      <div className="main">
        <div className="left">
          <AskFriends
            cities={cities}
            city={city}
            onCityChange={(c) => {
              setCity(c)
              setAnswer(null)
            }}
            onAsk={ask}
            loading={asking}
          />
          <AddRecs
            onAdded={(res) => {
              setRun(res.run)
              refresh()
            }}
          />
          <RunStatsCard run={run} />
        </div>

        <div className="right">
          <div>
            <div className="seg" role="tablist" aria-label="Which places to show">
              <button className={onlySaved ? '' : 'active'} onClick={() => setOnlySaved(false)}>
                <MapIcon size={14} /> All places <span className="count">{places.length}</span>
              </button>
              <button className={onlySaved ? 'active' : ''} onClick={() => setOnlySaved(true)}>
                <Bookmark size={14} /> Want to go <span className="count">{savedIds.size}</span>
              </button>
            </div>
            <PlaceMap places={shown} picks={picks} onSavedChange={markSaved} />
          </div>
          {asking && (
            <div className="card thinking">
              <span className="dots"><i /><i /><i /></span>
              <span className="hint">Reading what your friends said…</span>
            </div>
          )}
          {askError && <div className="notice error">{askError}</div>}
          {answer && <AnswerCard answer={answer} saved={savedIds} onSavedChange={markSaved} />}
          {answer && <TraceCard trace={answer.trace} title="How this answer was made" />}
        </div>
      </div>
    </div>
  )
}
