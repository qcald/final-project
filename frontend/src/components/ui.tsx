import { categoryColor, categoryIcon, RATING_BADGE, avatarColors } from '../catalog'
import type { Sentiment } from '../types'

export function Avatar({ name, size = 36 }: { name: string; size?: number }) {
  return (
    <span className="avatar" style={{ ...avatarColors(name), width: size, height: size, fontSize: size * 0.42 }}>
      {name[0]?.toUpperCase()}
    </span>
  )
}

export function CategoryTag({ category }: { category: string }) {
  const Icon = categoryIcon(category)
  const color = categoryColor(category)
  return (
    <span className="cat-tag" style={{ color, background: `${color}14` }}>
      <Icon size={12} strokeWidth={2.4} /> {category}
    </span>
  )
}

export function CategoryTile({ category, size = 44 }: { category: string; size?: number }) {
  const Icon = categoryIcon(category)
  const color = categoryColor(category)
  return (
    <span className="cat-tile" style={{ background: `${color}18`, color, width: size, height: size }}>
      <Icon size={size * 0.45} strokeWidth={2.2} />
    </span>
  )
}

export function Rating({ sentiment }: { sentiment: Sentiment }) {
  return <span className={`rating-badge sentiment-${sentiment}`}>{RATING_BADGE[sentiment]}</span>
}
