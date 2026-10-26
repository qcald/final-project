"""The three agents.

Intake   (LLM)  : messy pasted text -> structured recommendations (place, city, friend, quote).
Resolver (tool) : geocodes each place with OpenStreetMap and merges duplicates into the database.
                  Also used for posts people share in the app.
Answer   (LLM)  : answers a trip question using ONLY places friends recommended, citing who said it.
"""

import csv
import hashlib
import io
import json
import re
import time
import unicodedata

import requests

import config
import db
import safety
from llm import Run

CATEGORIES = ["food", "drinks", "coffee", "sight", "activity", "stay", "shop", "other"]
SENTIMENTS = ["love", "like", "mixed", "avoid"]

def _norm(s: str) -> str:
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", " ", s).strip()


# --------------------------------------------------------------------------------------
# Agent 1: Intake
# --------------------------------------------------------------------------------------

INTAKE_SYSTEM = (config.PROMPTS_DIR / "intake.md").read_text()

INTAKE_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "recs": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {
                "name": {"type": "string"},
                "name_is_guess": {"type": "boolean"},
                "city": {"type": "string"},
                "country": {"type": "string"},
                "category": {"type": "string", "enum": CATEGORIES},
                "friend": {"type": "string"},
                "quote": {"type": "string"},
                "sentiment": {"type": "string", "enum": SENTIMENTS},
            },
            "required": ["name", "name_is_guess", "city", "country", "category", "friend", "quote",
                         "sentiment"],
        }},
        "skipped_instructions": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["recs", "skipped_instructions"],
}


def intake(run: Run, text: str, default_friend: str) -> dict:
    """Clean the pasted text, then extract recommendations. Returns recs plus safety notes."""
    if len(text) > config.MAX_PASTE_CHARS:
        raise ValueError(f"Pasted text is {len(text):,} characters; the limit is "
                         f"{config.MAX_PASTE_CHARS:,}. Paste it in smaller pieces.")
    run.step("intake", "check", "Size check", f"{len(text):,} of {config.MAX_PASTE_CHARS:,} characters allowed")
    clean, n_pii = safety.scrub_pii(text)
    run.step("intake", "check", "Removed personal details",
             f"{n_pii} phone number(s) or email(s) replaced before the model sees the text")
    flagged = safety.find_injection(clean)
    run.step("intake", "check", "Hidden-instruction check",
             f"{len(flagged)} line(s) flagged; pasted text is wrapped in <pasted> tags as data")
    user = (f"Default friend name: {default_friend or 'Unknown friend'}\n\n"
            f"<pasted>\n{clean}\n</pasted>")
    out = run.call_json("intake", INTAKE_SYSTEM, user, INTAKE_SCHEMA)
    run.step("intake", "result", "Extracted recommendations",
             f"{len(out['recs'])} place(s); the model also refused {len(out['skipped_instructions'])} instruction line(s)")
    return {"recs": out["recs"], "pii_removed": n_pii, "flagged_lines": flagged,
            "skipped_instructions": out["skipped_instructions"]}


# --------------------------------------------------------------------------------------
# Agent 2: Resolver (deterministic tool: geocoding + de-duplication, no model tokens)
# --------------------------------------------------------------------------------------

_last_geocode = 0.0


def geocode(name: str, city: str, country: str) -> dict | None:
    global _last_geocode
    query = ", ".join(p for p in (name, city, country) if p)
    cache = json.loads(config.GEOCACHE_FILE.read_text()) if config.GEOCACHE_FILE.exists() else {}
    if query in cache:
        return cache[query]
    wait = 1.1 - (time.time() - _last_geocode)  # Nominatim allows 1 request per second
    if wait > 0:
        time.sleep(wait)
    try:
        r = requests.get(config.GEOCODER_URL, timeout=10,
                         params={"q": query, "format": "jsonv2", "limit": 1},
                         headers={"User-Agent": config.GEOCODER_USER_AGENT})
        r.raise_for_status()
        hits = r.json()
    except requests.RequestException:
        return None  # don't cache failures; try again next time
    finally:
        _last_geocode = time.time()
    hit = None
    if hits:
        h = hits[0]
        hit = {"osm_id": f"{h['osm_type']}/{h['osm_id']}", "lat": float(h["lat"]),
               "lon": float(h["lon"]), "address": h["display_name"]}
    cache[query] = hit
    config.GEOCACHE_FILE.write_text(json.dumps(cache, indent=1, ensure_ascii=False))
    return hit


def resolve_place(conn, name: str, city: str, country: str, category: str, name_is_guess: bool = False) -> dict:
    """Find this place in the database, or geocode it and add it. Returns the place row as a dict
    plus `is_new`."""
    geo = None if name_is_guess else geocode(name, city, country)
    key = geo["osm_id"] if geo else f"{_norm(name)}|{_norm(city)}"
    row = db.find_place(conn, key)
    if row is not None:
        return {**dict(row), "is_new": False}
    place = {
        "id": hashlib.sha1(key.encode()).hexdigest()[:8], "key": key,
        "name": name.strip(), "city": city.strip(), "category": category,
        # Posts don't ask for a country; take it from the end of the geocoded address
        "country": country.strip() or (geo["address"].rsplit(",", 1)[-1].strip() if geo else ""),
        "verified": int(geo is not None),
        "lat": geo["lat"] if geo else None, "lon": geo["lon"] if geo else None,
        "address": geo["address"] if geo else "",
    }
    db.insert_place(conn, place)
    return {**place, "is_new": True}


def resolve(conn, recs: list[dict], owner_id: int, author: dict | None = None) -> dict:
    """Geocode imported recs and save them as private to the user who imported them. Pass `author`
    (the user) when the recs are the user's own, e.g. their own Google Maps list."""
    added, merged, unverified = 0, 0, 0
    for rec in recs:
        place = resolve_place(conn, rec["name"], rec["city"], rec["country"], rec["category"],
                              rec["name_is_guess"])
        if place["is_new"]:
            added += 1
            unverified += not place["verified"]
        else:
            merged += 1
        db.insert_rec(conn, place_id=place["id"], owner_id=owner_id, author_id=author and author["id"],
                      friend_name=author["display_name"] if author else rec["friend"],
                      quote=rec["quote"].strip() or "Saved it on their list.", sentiment=rec["sentiment"],
                      shared=False)
    return {"added": added, "merged": merged, "unverified": unverified}


# --------------------------------------------------------------------------------------
# Agent 3: Answer
# --------------------------------------------------------------------------------------

ANSWER_SYSTEM = (config.PROMPTS_DIR / "answer.md").read_text()

ANSWER_SCHEMA = {
    "type": "object", "additionalProperties": False,
    "properties": {
        "summary": {"type": "string"},
        "picks": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "properties": {"place_id": {"type": "string"}, "why": {"type": "string"}},
            "required": ["place_id", "why"],
        }},
        "not_covered": {"type": "string"},
    },
    "required": ["summary", "picks", "not_covered"],
}


def answer(run: Run, question: str, places: list[dict]) -> dict:
    """`places` is already limited to what this user may see (see db.visible_places)."""
    cands = places[:config.MAX_CANDIDATES]
    run.step("answer", "check", "Gathered candidates",
             f"{len(cands)} place(s) you're allowed to see: your recs, your friends' posts, your imports")
    if not cands:
        return {"summary": "None of your friends have recommended anything here yet.", "picks": [],
                "not_covered": question, "dropped": [], "removed_sentences": []}
    slim = [{"id": p["id"], "name": p["name"], "city": p["city"], "category": p["category"],
             "friends_said": [f"{r['friend']} ({r['sentiment']}): {r['quote']}" for r in p["recs"]]}
            for p in cands]
    user = f"Question: {question}\n\nCandidate places:\n{json.dumps(slim, ensure_ascii=False)}"
    out = run.call_json("answer", ANSWER_SYSTEM, user, ANSWER_SCHEMA)

    # Defense against invented places: keep only picks whose id is a real candidate, and take the
    # friend attributions from the database rather than from the model.
    by_id = {p["id"]: p for p in cands}
    picks, dropped = [], []
    for pick in out["picks"]:
        place = by_id.get(pick["place_id"])
        if place is None:
            dropped.append(pick)
        else:
            picks.append({**pick, "place": place})

    run.step("answer", "check", "Invented-pick check",
             f"{len(picks)} pick(s) matched real candidates; {len(dropped)} blocked")

    # Second defense: the explanation text could still name a place no friend recommended
    # (e.g. a famous landmark). Drop any sentence that does.
    allowed = question + " " + json.dumps(slim, ensure_ascii=False)
    summary, removed = safety.strip_unlisted_mentions(out["summary"], allowed)
    for pick in picks:
        pick["why"], r = safety.strip_unlisted_mentions(pick["why"], allowed)
        removed += r
    run.step("answer", "check", "Unlisted-place check",
             f"{len(removed)} sentence(s) removed for naming a place no friend recommended")
    run.step("answer", "check", "Quotes from the database",
             "Friend names and quotes shown with each pick come from saved recs, not the model")
    return {"summary": summary, "picks": picks, "not_covered": out["not_covered"],
            "dropped": dropped, "removed_sentences": removed}


# --------------------------------------------------------------------------------------
# Google Maps saved lists (Google Takeout CSV: Title, Note, URL, ... , Comment)
# --------------------------------------------------------------------------------------

MAX_LIST_ROWS = 60


def google_maps_csv_to_text(csv_text: str, city: str) -> tuple[str, int]:
    """Turn a Takeout saved-list CSV into plain lines the Intake agent can read.
    Returns the text and how many rows were left out because the list was too long."""
    rows = [r for r in csv.DictReader(io.StringIO(csv_text.strip())) if (r.get("Title") or "").strip()]
    if not rows:
        raise ValueError("That doesn't look like a Google Maps list. Export it from Google Takeout "
                         "(Saved > your list.csv) and paste the whole file.")
    lines = [f"Google Maps saved list{f' for {city}' if city else ''}:"]
    for r in rows[:MAX_LIST_ROWS]:
        note = " ".join(x.strip() for x in (r.get("Note"), r.get("Comment")) if x and x.strip())
        lines.append(f"- {r['Title'].strip()}" + (f": {note}" if note else ""))
    return "\n".join(lines), max(0, len(rows) - MAX_LIST_ROWS)
