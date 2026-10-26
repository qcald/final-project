"""SQLite storage: users, friendships, places, and recommendations.

Who can see a recommendation:
- Posts (shared = 1) are visible to the author and the author's friends.
- Imported chats (shared = 0) are other people's words, so they stay private to the user who imported them.
"""

import json
import sqlite3
from contextlib import contextmanager

import config
from auth import hash_password

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY,
    username      TEXT NOT NULL UNIQUE,
    email         TEXT NOT NULL UNIQUE,
    display_name  TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS friendships (
    requester_id INTEGER NOT NULL REFERENCES users(id),
    addressee_id INTEGER NOT NULL REFERENCES users(id),
    status       TEXT NOT NULL CHECK (status IN ('pending', 'accepted')),
    created_at   TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (requester_id, addressee_id)
);
CREATE TABLE IF NOT EXISTS places (
    id       TEXT PRIMARY KEY,
    key      TEXT NOT NULL UNIQUE,
    name     TEXT NOT NULL,
    city     TEXT NOT NULL,
    country  TEXT NOT NULL,
    category TEXT NOT NULL,
    verified INTEGER NOT NULL,
    lat      REAL,
    lon      REAL,
    address  TEXT NOT NULL DEFAULT ''
);
CREATE TABLE IF NOT EXISTS recs (
    id          INTEGER PRIMARY KEY,
    place_id    TEXT NOT NULL REFERENCES places(id),
    owner_id    INTEGER NOT NULL REFERENCES users(id),
    author_id   INTEGER REFERENCES users(id),
    friend_name TEXT NOT NULL,
    quote       TEXT NOT NULL,
    sentiment   TEXT NOT NULL,
    shared      INTEGER NOT NULL,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS saves (
    user_id    INTEGER NOT NULL REFERENCES users(id),
    place_id   TEXT NOT NULL REFERENCES places(id),
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (user_id, place_id)
);
"""

# Demo accounts for the sample data. Everyone shares this test password (see README).
DEMO_PASSWORD = "friendrecs"
DEMO_USERS = [("maya", "Maya"), ("jordan", "Jordan"), ("priya", "Priya"), ("sam", "Sam"), ("dana", "Dana"),
              ("qcald", "Quinn")]  # qcald is the default friend for new accounts (config.DEFAULT_FRIEND)
DEMO_FRIENDS = [("maya", "jordan"), ("maya", "priya"), ("maya", "sam")]
DEMO_REQUESTS = [("dana", "maya")]  # Dana's request is waiting for Maya, so the accept flow can be tried


def demo_email(username: str) -> str:
    return f"{username}@example.com"  # example.com is reserved for examples, so these never reach anyone


@contextmanager
def connect():
    conn = sqlite3.connect(config.DB_FILE, timeout=30)  # geocoding can hold a write for a few seconds
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def _add_email_column(conn) -> None:
    """Databases made before emails were required lack the column. Add it, and give the demo
    accounts their emails. Other existing accounts keep working without one."""
    columns = [r["name"] for r in conn.execute("PRAGMA table_info(users)")]
    if "email" in columns:
        return
    conn.execute("ALTER TABLE users ADD COLUMN email TEXT")
    conn.execute("CREATE UNIQUE INDEX IF NOT EXISTS users_email ON users(email)")
    for username, _ in DEMO_USERS:
        conn.execute("UPDATE users SET email = ? WHERE username = ?", (demo_email(username), username))


def init_db() -> None:
    """Create the tables, and load the demo users and sample places into an empty database."""
    config.DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    with connect() as conn:
        conn.executescript(SCHEMA)
        _add_email_column(conn)
        if conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]:
            return
        ids = {}
        for username, name in DEMO_USERS:
            cur = conn.execute("INSERT INTO users (username, email, display_name, password_hash) VALUES (?, ?, ?, ?)",
                               (username, demo_email(username), name, hash_password(DEMO_PASSWORD)))
            ids[name] = cur.lastrowid
        for a, b in DEMO_FRIENDS:
            conn.execute("INSERT INTO friendships (requester_id, addressee_id, status) VALUES (?, ?, 'accepted')",
                         (ids[a.title()], ids[b.title()]))
        for a, b in DEMO_REQUESTS:
            conn.execute("INSERT INTO friendships (requester_id, addressee_id, status) VALUES (?, ?, 'pending')",
                         (ids[a.title()], ids[b.title()]))
        # Sample recs become posts by the matching demo user
        for p in json.loads(config.SAMPLE_PLACES_FILE.read_text()):
            conn.execute(
                "INSERT INTO places (id, key, name, city, country, category, verified, lat, lon, address) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (p["id"], p["key"], p["name"], p["city"], p["country"], p["category"], int(p["verified"]),
                 p["lat"], p["lon"], p["address"]))
            for r in p["recs"]:
                uid = ids.get(r["friend"])
                if uid:
                    conn.execute(
                        "INSERT INTO recs (place_id, owner_id, author_id, friend_name, quote, sentiment, shared) "
                        "VALUES (?, ?, ?, ?, ?, ?, 1)", (p["id"], uid, uid, r["friend"], r["quote"], r["sentiment"]))


# --- Users and friends ---------------------------------------------------------------


def user_to_dict(row: sqlite3.Row) -> dict:
    return {"id": row["id"], "username": row["username"], "display_name": row["display_name"]}


def get_user(conn, *, user_id: int | None = None, username: str | None = None,
             email: str | None = None) -> sqlite3.Row | None:
    if user_id is not None:
        return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if email is not None:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    return conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()


def friend_ids(conn, user_id: int) -> list[int]:
    rows = conn.execute(
        """SELECT CASE WHEN requester_id = ? THEN addressee_id ELSE requester_id END AS fid
           FROM friendships WHERE status = 'accepted' AND ? IN (requester_id, addressee_id)""",
        (user_id, user_id)).fetchall()
    return [r["fid"] for r in rows]


def befriend(conn, a: int, b: int) -> None:
    """Make two users friends, whatever state their friendship was in."""
    if friendship(conn, a, b) is None:
        conn.execute("INSERT INTO friendships (requester_id, addressee_id, status) VALUES (?, ?, 'accepted')", (a, b))
    else:
        conn.execute("UPDATE friendships SET status = 'accepted' WHERE (requester_id = ? AND addressee_id = ?) "
                     "OR (requester_id = ? AND addressee_id = ?)", (a, b, b, a))


def friendship(conn, a: int, b: int) -> sqlite3.Row | None:
    return conn.execute(
        "SELECT * FROM friendships WHERE (requester_id = ? AND addressee_id = ?) OR (requester_id = ? AND addressee_id = ?)",
        (a, b, b, a)).fetchone()


# --- Places and recs -----------------------------------------------------------------


def find_place(conn, key: str) -> sqlite3.Row | None:
    return conn.execute("SELECT * FROM places WHERE key = ?", (key,)).fetchone()


def insert_place(conn, place: dict) -> None:
    conn.execute(
        "INSERT INTO places (id, key, name, city, country, category, verified, lat, lon, address) "
        "VALUES (:id, :key, :name, :city, :country, :category, :verified, :lat, :lon, :address)", place)


def insert_rec(conn, *, place_id: str, owner_id: int, author_id: int | None, friend_name: str,
               quote: str, sentiment: str, shared: bool) -> int:
    """Add a rec unless the same person already said the same thing about this place.
    Returns the rec's id either way."""
    dup = conn.execute(
        "SELECT id FROM recs WHERE place_id = ? AND owner_id = ? AND friend_name = ? AND quote = ?",
        (place_id, owner_id, friend_name, quote)).fetchone()
    if dup:
        return dup["id"]
    cur = conn.execute(
        "INSERT INTO recs (place_id, owner_id, author_id, friend_name, quote, sentiment, shared) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)", (place_id, owner_id, author_id, friend_name, quote, sentiment, int(shared)))
    return cur.lastrowid


def _visible_recs_sql(user_id: int, friends: list[int]) -> tuple[str, list]:
    marks = ",".join("?" * len(friends)) or "NULL"
    return (f"(r.owner_id = ? OR (r.shared = 1 AND r.owner_id IN ({marks})))", [user_id, *friends])


def visible_places(conn, user_id: int, city: str = "") -> list[dict]:
    """Every place this user can see, with only the recs they're allowed to see."""
    where, params = _visible_recs_sql(user_id, friend_ids(conn, user_id))
    if city:
        where += " AND p.city = ?"
        params.append(city)
    rows = conn.execute(
        f"""SELECT p.*, r.id AS rec_id, r.friend_name, r.quote, r.sentiment, r.shared, r.author_id, r.created_at
            FROM recs r JOIN places p ON p.id = r.place_id WHERE {where} ORDER BY p.name, r.id""",
        params).fetchall()
    saved = saved_ids(conn, user_id)
    places: dict[str, dict] = {}
    for row in rows:
        p = places.setdefault(row["id"], {
            "id": row["id"], "name": row["name"], "city": row["city"], "country": row["country"],
            "category": row["category"], "verified": bool(row["verified"]), "lat": row["lat"],
            "lon": row["lon"], "address": row["address"], "saved": row["id"] in saved, "recs": []})
        p["recs"].append({"friend": "You" if row["author_id"] == user_id else row["friend_name"],
                          "quote": row["quote"], "sentiment": row["sentiment"],
                          "on_app": row["author_id"] is not None})
    return list(places.values())


def feed(conn, user_id: int, limit: int = 50) -> list[dict]:
    """Newest posts from the user and their friends."""
    ids = [user_id, *friend_ids(conn, user_id)]
    marks = ",".join("?" * len(ids))
    rows = conn.execute(
        f"""SELECT r.id, r.quote, r.sentiment, r.created_at, u.username, u.display_name,
                   p.id AS place_id, p.name, p.city, p.country, p.category, p.lat, p.lon
            FROM recs r JOIN users u ON u.id = r.author_id JOIN places p ON p.id = r.place_id
            WHERE r.shared = 1 AND r.author_id IN ({marks})
            ORDER BY r.created_at DESC, r.id DESC LIMIT ?""", [*ids, limit]).fetchall()
    me = get_user(conn, user_id=user_id)["username"]
    saved = saved_ids(conn, user_id)
    return [{"id": r["id"], "quote": r["quote"], "sentiment": r["sentiment"], "created_at": r["created_at"],
             "author": {"username": r["username"], "display_name": r["display_name"],
                        "is_me": r["username"] == me},
             "place": {"id": r["place_id"], "name": r["name"], "city": r["city"], "country": r["country"],
                       "category": r["category"], "saved": r["place_id"] in saved}}
            for r in rows]


def get_post(conn, post_id: int, user_id: int) -> dict | None:
    """One post, as the feed shows it, if this user can see it."""
    return next((p for p in feed(conn, user_id, limit=10_000) if p["id"] == post_id), None)


# --- Want-to-go saves ---------------------------------------------------------------


def saved_ids(conn, user_id: int) -> set[str]:
    return {r["place_id"] for r in conn.execute("SELECT place_id FROM saves WHERE user_id = ?", (user_id,))}


def can_see_place(conn, user_id: int, place_id: str) -> bool:
    where, params = _visible_recs_sql(user_id, friend_ids(conn, user_id))
    return conn.execute(f"SELECT 1 FROM recs r WHERE r.place_id = ? AND {where} LIMIT 1",
                        [place_id, *params]).fetchone() is not None
