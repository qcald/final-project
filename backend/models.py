"""Request and response shapes for the API."""

import re
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, field_validator

import config

Category = Literal["food", "drinks", "coffee", "sight", "activity", "stay", "shop", "other"]
Sentiment = Literal["love", "like", "mixed", "avoid"]


# --- Accounts and friends ------------------------------------------------------------


class User(BaseModel):
    id: int
    username: str
    display_name: str


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=30)
    email: EmailStr
    display_name: str = Field(min_length=1, max_length=40)
    password: str = Field(min_length=8, max_length=128)
    invite: str = ""  # an invite code from a friend's link; you become friends on signup

    @field_validator("username")
    @classmethod
    def username_chars(cls, v: str) -> str:
        v = v.strip().lower()
        if not re.fullmatch(r"[a-z0-9_]+", v):
            raise ValueError("Usernames can only use letters, numbers, and underscores.")
        return v


class LoginRequest(BaseModel):
    username: str  # a username or an email
    password: str


class AuthResponse(BaseModel):
    token: str
    user: User


class FriendRequest(BaseModel):
    username: str


class InviteInfo(BaseModel):
    code: str
    inviter: User


class InviteRequest(BaseModel):
    code: str


class FriendsResponse(BaseModel):
    friends: list[User]
    incoming: list[User]  # requests waiting for you to accept
    outgoing: list[User]  # requests you sent


# --- Places and recs -----------------------------------------------------------------


class Rec(BaseModel):
    friend: str
    quote: str
    sentiment: str
    on_app: bool


class Place(BaseModel):
    id: str
    name: str
    city: str
    country: str
    category: str
    verified: bool
    lat: float | None
    lon: float | None
    address: str
    saved: bool
    recs: list[Rec]


class TraceStep(BaseModel):
    agent: str
    kind: str  # "check", "tool", "model", or "result"
    title: str
    detail: str
    at_ms: int


class RunStats(BaseModel):
    calls: int
    input_tokens: int
    cached_input_tokens: int
    output_tokens: int
    seconds: float
    cost_usd: float | None


class AddRecsRequest(BaseModel):
    text: str = Field(min_length=1, max_length=config.MAX_PASTE_CHARS)
    friend: str = Field(default="", max_length=80)


class PostRequest(BaseModel):
    place: str = Field(min_length=1, max_length=120)
    city: str = Field(min_length=1, max_length=80)
    category: Category
    sentiment: Sentiment
    note: str = Field(min_length=1, max_length=280)


class FeedPlace(BaseModel):
    id: str
    name: str
    city: str
    country: str
    category: str
    saved: bool


class FeedAuthor(BaseModel):
    username: str
    display_name: str
    is_me: bool


class FeedItem(BaseModel):
    id: int
    quote: str
    sentiment: str
    created_at: str
    author: FeedAuthor
    place: FeedPlace


class PostResponse(BaseModel):
    post: FeedItem
    verified: bool
    address: str  # where the Resolver pinned it, so the poster can catch a wrong match


class PostUpdate(BaseModel):
    sentiment: Sentiment
    note: str = Field(min_length=1, max_length=280)


class GoogleMapsImportRequest(BaseModel):
    csv: str = Field(min_length=1, max_length=200_000)
    owner: str = Field(default="", max_length=80)  # whose list it is; blank means yours
    city: str = Field(default="", max_length=80)


class ImportResponse(BaseModel):
    found: int
    added: int
    merged: int
    unverified: int
    pii_removed: int
    ignored_lines: list[str]
    skipped_rows: int = 0
    run: RunStats
    trace: list[TraceStep]


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=1000)
    city: str = ""


class Pick(BaseModel):
    why: str
    place: Place


class AskResponse(BaseModel):
    summary: str
    picks: list[Pick]
    not_covered: str
    blocked: int  # picks that weren't real candidates
    removed_sentences: list[str]  # explanation sentences that named places no friend recommended
    run: RunStats
    trace: list[TraceStep]
