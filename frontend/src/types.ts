export type Sentiment = 'love' | 'like' | 'mixed' | 'avoid'

export const CATEGORIES = ['food', 'drinks', 'coffee', 'sight', 'activity', 'stay', 'shop', 'other'] as const
export type Category = (typeof CATEGORIES)[number]

export interface User {
  id: number
  username: string
  display_name: string
}

export interface FriendsResponse {
  friends: User[]
  incoming: User[]
  outgoing: User[]
}

export interface Rec {
  friend: string
  quote: string
  sentiment: Sentiment
  on_app: boolean
}

export interface Place {
  id: string
  name: string
  city: string
  country: string
  category: string
  verified: boolean
  lat: number | null
  lon: number | null
  address: string
  saved: boolean
  recs: Rec[]
}

export interface TraceStep {
  agent: string
  kind: 'check' | 'tool' | 'model' | 'result'
  title: string
  detail: string
  at_ms: number
}

export interface RunStats {
  calls: number
  input_tokens: number
  cached_input_tokens: number
  output_tokens: number
  seconds: number
  cost_usd: number | null
}

export interface AddRecsResponse {
  found: number
  added: number
  merged: number
  unverified: number
  pii_removed: number
  ignored_lines: string[]
  skipped_rows: number
  run: RunStats
  trace: TraceStep[]
}

export interface Pick {
  why: string
  place: Place
}

export interface AskResponse {
  summary: string
  picks: Pick[]
  not_covered: string
  blocked: number
  removed_sentences: string[]
  run: RunStats
  trace: TraceStep[]
}

export interface FeedItem {
  id: number
  quote: string
  sentiment: Sentiment
  created_at: string
  author: { username: string; display_name: string; is_me: boolean }
  place: { id: string; name: string; city: string; country: string; category: string; saved: boolean }
}

export interface NewPost {
  place: string
  city: string
  category: Category
  sentiment: Sentiment
  note: string
}

export interface InviteInfo {
  code: string
  inviter: User
}
