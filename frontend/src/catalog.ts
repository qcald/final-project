import {
  BedDouble,
  Coffee,
  Landmark,
  MapPin,
  ShoppingBag,
  Ticket,
  Utensils,
  Wine,
  type LucideIcon,
} from 'lucide-react'
import type { Sentiment } from './types'

export const CATEGORY_COLORS: Record<string, string> = {
  food: '#f0643c',
  drinks: '#c04f8a',
  coffee: '#9a6b4f',
  sight: '#3b6fe0',
  activity: '#14a38b',
  stay: '#7b61d9',
  shop: '#e09a2d',
  other: '#8a8f98',
}

export const CATEGORY_ICONS: Record<string, LucideIcon> = {
  food: Utensils,
  drinks: Wine,
  coffee: Coffee,
  sight: Landmark,
  activity: Ticket,
  stay: BedDouble,
  shop: ShoppingBag,
  other: MapPin,
}

export const SENTIMENT_LABEL: Record<Sentiment, string> = {
  love: 'loves it',
  like: 'likes it',
  mixed: 'mixed',
  avoid: 'says skip',
}

/** Short rating labels for posts and the post form. */
export const RATING_BADGE: Record<Sentiment, string> = {
  love: 'Love it',
  like: 'Like it',
  mixed: 'Mixed',
  avoid: 'Skip it',
}

export const categoryColor = (category: string) => CATEGORY_COLORS[category] ?? CATEGORY_COLORS.other
export const categoryIcon = (category: string) => CATEGORY_ICONS[category] ?? MapPin

// Soft background / strong text pairs for avatars, picked by name so each person keeps one color
const AVATAR_COLORS: [string, string][] = [
  ['#ffe4dc', '#c2410c'],
  ['#e0ecff', '#1d4ed8'],
  ['#dcf5ec', '#047857'],
  ['#f1e4ff', '#7e22ce'],
  ['#fff1cc', '#a16207'],
  ['#ffe0ef', '#be185d'],
  ['#dff4fb', '#0e7490'],
]

export function avatarColors(name: string): { background: string; color: string } {
  let h = 0
  for (const ch of name.toLowerCase()) h = (h * 31 + ch.charCodeAt(0)) >>> 0
  const [background, color] = AVATAR_COLORS[h % AVATAR_COLORS.length]
  return { background, color }
}
