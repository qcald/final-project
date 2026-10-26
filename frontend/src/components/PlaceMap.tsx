import L from 'leaflet'
import { useEffect, useMemo, type CSSProperties } from 'react'
import { renderToStaticMarkup } from 'react-dom/server'
import { MapContainer, Marker, Popup, TileLayer, useMap } from 'react-leaflet'
import { CATEGORY_COLORS, categoryColor, categoryIcon } from '../catalog'
import type { Place } from '../types'
import SaveButton from './SaveButton'
import { Avatar, CategoryTag, Rating } from './ui'

type Located = Place & { lat: number; lon: number }

/** Zoom the map to whatever places are showing (or to the picks, after an answer). */
function FitToPlaces({ places }: { places: Located[] }) {
  const map = useMap()
  // Re-zoom only when the set of places changes, not when one is saved or edited
  const key = places.map((p) => p.id).join(',')
  useEffect(() => {
    if (places.length === 0) return
    if (places.length === 1) map.setView([places[0].lat, places[0].lon], 14)
    else map.fitBounds(places.map((p) => [p.lat, p.lon] as [number, number]), { padding: [50, 50] })
  }, [map, key])
  return null
}

/** A teardrop pin in the category color: numbered for answer picks, an icon otherwise. */
function pinIcon(category: string, number: number | null, dim: boolean) {
  const Icon = categoryIcon(category)
  const size = number ? 34 : 26
  const html = renderToStaticMarkup(
    <div className={`pin${number ? ' big' : ''}${dim ? ' dim' : ''}`} style={{ '--c': categoryColor(category) } as CSSProperties}>
      {number ? <span>{number}</span> : <Icon size={12} strokeWidth={2.8} />}
    </div>,
  )
  return L.divIcon({ html, className: 'pin-wrap', iconSize: [size, size], iconAnchor: [size / 2, size], popupAnchor: [0, -size] })
}

export default function PlaceMap({ places, picks, onSavedChange }: {
  places: Place[]
  picks: string[]
  onSavedChange: (placeId: string, saved: boolean) => void
}) {
  // Memoized so the map only re-zooms when the places or picks change, not on every render
  const located = useMemo(
    () => places.filter((p): p is Located => p.lat !== null && p.lon !== null),
    [places],
  )
  const focus = useMemo(() => {
    const picked = located.filter((p) => picks.includes(p.id))
    return picked.length ? picked : located
  }, [located, picks])
  const used = Object.keys(CATEGORY_COLORS).filter((c) => located.some((p) => p.category === c))

  return (
    <div className="card map-card">
      <MapContainer center={[30, 0]} zoom={2} scrollWheelZoom className="map">
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        <FitToPlaces places={focus} />
        {located.map((p) => {
          const n = picks.indexOf(p.id)
          return (
            <Marker
              key={p.id}
              position={[p.lat, p.lon]}
              icon={pinIcon(p.category, n >= 0 ? n + 1 : null, picks.length > 0 && n < 0)}
              zIndexOffset={n >= 0 ? 1000 - n : 0}
            >
              <Popup>
                <div className="popup-title">
                  {p.name} <CategoryTag category={p.category} />
                </div>
                <SaveButton key={`${p.id}-${p.saved}`} placeId={p.id} saved={p.saved}
                            onChange={(saved) => onSavedChange(p.id, saved)} />
                {p.recs.map((r, i) => (
                  <div key={i} className="popup-rec">
                    <Avatar name={r.friend} size={22} />
                    <div>
                      <b>{r.friend}</b> <Rating sentiment={r.sentiment} />
                      <div>“{r.quote}”</div>
                    </div>
                  </div>
                ))}
              </Popup>
            </Marker>
          )
        })}
      </MapContainer>
      <div className="map-count">
        {located.length} place{located.length === 1 ? '' : 's'}
        {places.length > located.length && ` · ${places.length - located.length} not on map`}
      </div>
      {used.length > 0 && (
        <div className="map-legend">
          {used.map((c) => (
            <span key={c}>
              <i style={{ background: CATEGORY_COLORS[c] }} />
              {c}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
