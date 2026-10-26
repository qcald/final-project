import { getToken } from './auth'
import type {
  AddRecsResponse,
  AskResponse,
  FeedItem,
  FriendsResponse,
  InviteInfo,
  NewPost,
  Place,
  Sentiment,
} from './types'

function authHeaders(): Record<string, string> {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

async function errorDetail(res: Response): Promise<string> {
  try {
    const body = await res.json()
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail) && body.detail[0]?.msg) {
      return body.detail[0].msg.replace(/^Value error,\s*/, '')
    }
  } catch {
    /* ignore */
  }
  return 'Something went wrong. Please try again.'
}

async function getJson<T>(url: string): Promise<T> {
  const res = await fetch(url, { headers: authHeaders() })
  if (!res.ok) throw new Error(await errorDetail(res))
  return res.json() as Promise<T>
}

async function sendJson<T>(url: string, body: unknown, method = 'POST'): Promise<T> {
  const res = await fetch(url, {
    method,
    headers: { 'Content-Type': 'application/json', ...authHeaders() },
    body: body === undefined ? undefined : JSON.stringify(body),
  })
  if (!res.ok) throw new Error(await errorDetail(res))
  return res.json() as Promise<T>
}

export const fetchPlaces = (city: string) =>
  getJson<Place[]>(`/api/places${city ? `?city=${encodeURIComponent(city)}` : ''}`)
export const fetchCities = () => getJson<string[]>('/api/cities')

export const addRecs = (text: string, friend: string) =>
  sendJson<AddRecsResponse>('/api/recs', { text, friend })
export const askFriends = (question: string, city: string) =>
  sendJson<AskResponse>('/api/ask', { question, city })

export const fetchFeed = () => getJson<FeedItem[]>('/api/feed')
export const createPost = (post: NewPost) =>
  sendJson<{ post: FeedItem; verified: boolean; address: string }>('/api/posts', post)
export const editPost = (id: number, sentiment: Sentiment, note: string) =>
  sendJson<FeedItem>(`/api/posts/${id}`, { sentiment, note }, 'PATCH')
export const deletePost = (id: number) => sendJson<{ status: string }>(`/api/posts/${id}`, undefined, 'DELETE')

export const setSaved = (placeId: string, saved: boolean) =>
  sendJson<{ saved: boolean }>(`/api/saves/${encodeURIComponent(placeId)}`, undefined, saved ? 'PUT' : 'DELETE')

export const importGoogleMaps = (csv: string, owner: string, city: string) =>
  sendJson<AddRecsResponse>('/api/import/google-maps', { csv, owner, city })

export const fetchMyInvite = () => getJson<InviteInfo>('/api/invite')
export const fetchInviteInfo = (code: string) => getJson<InviteInfo>(`/api/invite/${encodeURIComponent(code)}`)
export const acceptInvite = (code: string) => sendJson<{ status: string }>('/api/invite/accept', { code })

export const fetchFriends = () => getJson<FriendsResponse>('/api/friends')
export const sendFriendRequest = (username: string) =>
  sendJson<{ status: 'pending' | 'accepted' }>('/api/friends/request', { username })
export const acceptFriendRequest = (username: string) =>
  sendJson<{ status: 'accepted' }>('/api/friends/accept', { username })
