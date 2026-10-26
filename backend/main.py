"""Friend Recs API: accounts, friends, posts and feed, the place map, importing chats, and asking friends.

Run from the backend folder:
    uvicorn main:app --reload --port 8000
"""

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse

import agents
import config
import db
from auth import create_invite_code, create_token, hash_password, verify_invite_code, verify_password, verify_token
from llm import Run
from models import (
    AddRecsRequest,
    AskRequest,
    AskResponse,
    AuthResponse,
    FeedItem,
    FriendRequest,
    FriendsResponse,
    GoogleMapsImportRequest,
    ImportResponse,
    InviteInfo,
    InviteRequest,
    LoginRequest,
    Place,
    PostRequest,
    PostResponse,
    PostUpdate,
    RegisterRequest,
    User,
)

FRONTEND_URL = "http://localhost:5173"
# The built React app. If it's there, this server serves it, so the app runs with Python alone.
FRONTEND_DIST = config.PROJECT_DIR / "frontend" / "dist"

app = FastAPI(title="Friend Recs API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

db.init_db()


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok"}


# --- Accounts -------------------------------------------------------------------------


def current_user(authorization: str | None = Header(default=None)) -> dict:
    """Resolve the bearer token in the Authorization header to a user."""
    user_id = verify_token(authorization.removeprefix("Bearer ").strip()) if authorization else None
    if user_id is not None:
        with db.connect() as conn:
            row = db.get_user(conn, user_id=user_id)
        if row is not None:
            return db.user_to_dict(row)
    raise HTTPException(status_code=401, detail="Please log in.")


@app.post("/api/auth/register")
def register(body: RegisterRequest) -> AuthResponse:
    email = body.email.lower()
    with db.connect() as conn:
        if db.get_user(conn, username=body.username):
            raise HTTPException(409, "That username is taken.")
        if db.get_user(conn, email=email):
            raise HTTPException(409, "An account with that email already exists.")
        cur = conn.execute("INSERT INTO users (username, email, display_name, password_hash) VALUES (?, ?, ?, ?)",
                           (body.username, email, body.display_name.strip(), hash_password(body.password)))
        row = db.get_user(conn, user_id=cur.lastrowid)
        inviter_id = verify_invite_code(body.invite) if body.invite else None
        if inviter_id is not None and db.get_user(conn, user_id=inviter_id):
            db.befriend(conn, inviter_id, row["id"])
        default_friend = db.get_user(conn, username=config.DEFAULT_FRIEND)
        if default_friend is not None and default_friend["id"] != row["id"]:
            db.befriend(conn, default_friend["id"], row["id"])
    return AuthResponse(token=create_token(row["id"]), user=db.user_to_dict(row))


@app.post("/api/auth/login")
def login(body: LoginRequest) -> AuthResponse:
    login_id = body.username.strip().lower()
    with db.connect() as conn:
        row = db.get_user(conn, email=login_id) if "@" in login_id else db.get_user(conn, username=login_id)
    if row is None or not verify_password(body.password, row["password_hash"]):
        raise HTTPException(401, "Incorrect username, email, or password.")
    return AuthResponse(token=create_token(row["id"]), user=db.user_to_dict(row))


@app.get("/api/auth/me")
def me(user: dict = Depends(current_user)) -> dict:
    return {"user": user}


# --- Friends --------------------------------------------------------------------------


@app.get("/api/friends")
def list_friends(user: dict = Depends(current_user)) -> FriendsResponse:
    uid = user["id"]
    with db.connect() as conn:
        rows = conn.execute(
            """SELECT f.requester_id, f.status, u.id, u.username, u.display_name FROM friendships f
               JOIN users u ON u.id = CASE WHEN f.requester_id = ? THEN f.addressee_id ELSE f.requester_id END
               WHERE ? IN (f.requester_id, f.addressee_id) ORDER BY u.display_name""", (uid, uid)).fetchall()
    out = FriendsResponse(friends=[], incoming=[], outgoing=[])
    for r in rows:
        u = User(id=r["id"], username=r["username"], display_name=r["display_name"])
        if r["status"] == "accepted":
            out.friends.append(u)
        elif r["requester_id"] == uid:
            out.outgoing.append(u)
        else:
            out.incoming.append(u)
    return out


@app.post("/api/friends/request")
def send_friend_request(body: FriendRequest, user: dict = Depends(current_user)) -> dict:
    with db.connect() as conn:
        other = db.get_user(conn, username=body.username.strip().lower().lstrip("@"))
        if other is None:
            raise HTTPException(404, "No one has that username.")
        if other["id"] == user["id"]:
            raise HTTPException(400, "You can't add yourself.")
        existing = db.friendship(conn, user["id"], other["id"])
        if existing is not None:
            if existing["status"] == "accepted":
                raise HTTPException(409, f"You're already friends with {other['display_name']}.")
            if existing["requester_id"] == other["id"]:  # they already asked you, so this accepts it
                conn.execute("UPDATE friendships SET status = 'accepted' WHERE requester_id = ? AND addressee_id = ?",
                             (other["id"], user["id"]))
                return {"status": "accepted"}
            raise HTTPException(409, "You already sent a request.")
        conn.execute("INSERT INTO friendships (requester_id, addressee_id, status) VALUES (?, ?, 'pending')",
                     (user["id"], other["id"]))
    return {"status": "pending"}


@app.post("/api/friends/accept")
def accept_friend_request(body: FriendRequest, user: dict = Depends(current_user)) -> dict:
    with db.connect() as conn:
        other = db.get_user(conn, username=body.username)
        updated = other and conn.execute(
            "UPDATE friendships SET status = 'accepted' WHERE requester_id = ? AND addressee_id = ? AND status = 'pending'",
            (other["id"], user["id"])).rowcount
    if not updated:
        raise HTTPException(404, "No pending request from that person.")
    return {"status": "accepted"}


# --- Invite links ---------------------------------------------------------------------


@app.get("/api/invite")
def my_invite(user: dict = Depends(current_user)) -> InviteInfo:
    """Your invite code. Anyone who opens your link and signs up (or accepts) becomes your friend."""
    return InviteInfo(code=create_invite_code(user["id"]), inviter=user)


@app.get("/api/invite/{code}")
def invite_info(code: str) -> InviteInfo:
    """Who sent this invite. No login needed, so the invite page can greet new people."""
    inviter_id = verify_invite_code(code)
    with db.connect() as conn:
        row = db.get_user(conn, user_id=inviter_id) if inviter_id is not None else None
    if row is None:
        raise HTTPException(404, "This invite link isn't valid.")
    return InviteInfo(code=code, inviter=db.user_to_dict(row))


@app.post("/api/invite/accept")
def accept_invite(body: InviteRequest, user: dict = Depends(current_user)) -> dict:
    inviter_id = verify_invite_code(body.code)
    if inviter_id is None:
        raise HTTPException(404, "This invite link isn't valid.")
    if inviter_id == user["id"]:
        raise HTTPException(400, "That's your own invite link.")
    with db.connect() as conn:
        if db.get_user(conn, user_id=inviter_id) is None:
            raise HTTPException(404, "This invite link isn't valid.")
        db.befriend(conn, inviter_id, user["id"])
    return {"status": "accepted"}


# --- Posts and feed -------------------------------------------------------------------


@app.post("/api/posts")
def create_post(body: PostRequest, user: dict = Depends(current_user)) -> PostResponse:
    """Share a recommendation with your friends. The Resolver geocodes it; no model call."""
    with db.connect() as conn:
        place = agents.resolve_place(conn, body.place, body.city, "", body.category)
        post_id = db.insert_rec(conn, place_id=place["id"], owner_id=user["id"], author_id=user["id"],
                                friend_name=user["display_name"], quote=body.note.strip(),
                                sentiment=body.sentiment, shared=True)
        post = db.get_post(conn, post_id, user["id"])
    return PostResponse(post=post, verified=bool(place["verified"]), address=place["address"])


def _own_post(conn, post_id: int, user_id: int) -> None:
    row = conn.execute("SELECT author_id, shared FROM recs WHERE id = ?", (post_id,)).fetchone()
    if row is None or not row["shared"]:
        raise HTTPException(404, "Post not found.")
    if row["author_id"] != user_id:
        raise HTTPException(403, "You can only change your own posts.")


@app.patch("/api/posts/{post_id}")
def edit_post(post_id: int, body: PostUpdate, user: dict = Depends(current_user)) -> FeedItem:
    with db.connect() as conn:
        _own_post(conn, post_id, user["id"])
        conn.execute("UPDATE recs SET quote = ?, sentiment = ? WHERE id = ?",
                     (body.note.strip(), body.sentiment, post_id))
        return db.get_post(conn, post_id, user["id"])


@app.delete("/api/posts/{post_id}")
def delete_post(post_id: int, user: dict = Depends(current_user)) -> dict:
    with db.connect() as conn:
        _own_post(conn, post_id, user["id"])
        conn.execute("DELETE FROM recs WHERE id = ?", (post_id,))
    return {"status": "deleted"}


@app.get("/api/feed")
def get_feed(user: dict = Depends(current_user)) -> list[FeedItem]:
    with db.connect() as conn:
        return db.feed(conn, user["id"])


# --- Want-to-go saves ------------------------------------------------------------------


@app.put("/api/saves/{place_id}")
def save_place(place_id: str, user: dict = Depends(current_user)) -> dict:
    with db.connect() as conn:
        if not db.can_see_place(conn, user["id"], place_id):
            raise HTTPException(404, "Place not found.")
        conn.execute("INSERT OR IGNORE INTO saves (user_id, place_id) VALUES (?, ?)", (user["id"], place_id))
    return {"saved": True}


@app.delete("/api/saves/{place_id}")
def unsave_place(place_id: str, user: dict = Depends(current_user)) -> dict:
    with db.connect() as conn:
        conn.execute("DELETE FROM saves WHERE user_id = ? AND place_id = ?", (user["id"], place_id))
    return {"saved": False}


# --- Map, import, ask -----------------------------------------------------------------


@app.get("/api/places")
def list_places(city: str = "", user: dict = Depends(current_user)) -> list[Place]:
    with db.connect() as conn:
        return db.visible_places(conn, user["id"], city)


@app.get("/api/cities")
def list_cities(user: dict = Depends(current_user)) -> list[str]:
    with db.connect() as conn:
        return sorted({p["city"] for p in db.visible_places(conn, user["id"])})


def _import(text: str, default_friend: str, user: dict, kind: str, own: bool = False) -> ImportResponse:
    """Intake agent extracts recommendations; the Resolver geocodes and saves them, private to you."""
    run = Run(kind)
    try:
        out = agents.intake(run, text, default_friend)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:  # missing key, API error, call limit
        raise HTTPException(502, f"The Intake agent failed: {e}")
    with db.connect() as conn:
        counts = agents.resolve(conn, out["recs"], user["id"], author=user if own else None)
    run.step("resolver", "tool", "Geocoded and saved",
             f"{counts['added']} new place(s), {counts['merged']} merged with existing, "
             f"{counts['unverified']} not found on OpenStreetMap; saved as private to you")
    # The regex check and the model can both report the same line (one with the "Name:" prefix)
    ignored = list(out["flagged_lines"])
    for line in out["skipped_instructions"]:
        if not any(line in kept or kept in line for kept in ignored):
            ignored.append(line)
    return ImportResponse(found=len(out["recs"]), pii_removed=out["pii_removed"], ignored_lines=ignored,
                          run=run.totals(), trace=run.trace, **counts)


@app.post("/api/recs")
def add_recs(req: AddRecsRequest, user: dict = Depends(current_user)) -> ImportResponse:
    """Import a pasted group chat or note."""
    return _import(req.text, req.friend.strip(), user, "add")


@app.post("/api/import/google-maps")
def import_google_maps(req: GoogleMapsImportRequest, user: dict = Depends(current_user)) -> ImportResponse:
    """Import a Google Maps saved list (Google Takeout CSV). Blank owner means it's your own list."""
    try:
        text, skipped = agents.google_maps_csv_to_text(req.csv, req.city.strip())
    except (ValueError, KeyError) as e:
        raise HTTPException(400, str(e).strip("'"))
    owner = req.owner.strip()
    res = _import(text, owner or user["display_name"], user, "google_maps", own=not owner)
    res.skipped_rows = skipped
    return res


@app.post("/api/ask")
def ask(req: AskRequest, user: dict = Depends(current_user)) -> AskResponse:
    """Answer agent picks only from places this user can see; invented picks are blocked."""
    run = Run("ask")
    with db.connect() as conn:
        places = db.visible_places(conn, user["id"], req.city)
    try:
        out = agents.answer(run, req.question, places)
    except Exception as e:
        raise HTTPException(502, f"The Answer agent failed: {e}")
    return AskResponse(summary=out["summary"], picks=out["picks"], not_covered=out["not_covered"],
                       blocked=len(out["dropped"]), removed_sentences=out["removed_sentences"],
                       run=run.totals(), trace=run.trace)


# --- The React app ----------------------------------------------------------------------


@app.get("/{path:path}", include_in_schema=False)
def frontend(path: str):
    """Serve the built React app (any non-API path gets index.html so client-side routes work).
    Without a build, send browsers to the Vite dev server instead."""
    if path.startswith("api/"):
        raise HTTPException(404, "Not found")
    if not FRONTEND_DIST.exists():
        return RedirectResponse(FRONTEND_URL)
    file = (FRONTEND_DIST / path).resolve()
    if path and file.is_file() and FRONTEND_DIST.resolve() in file.parents:
        return FileResponse(file)
    return FileResponse(FRONTEND_DIST / "index.html")
