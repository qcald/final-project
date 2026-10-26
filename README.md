# Friend Recs

Travel recommendations from people you trust. Share your own picks with friends, pull your friends'
old recs out of group chats and Google Maps lists, see them all on a map, and ask for a plan that
only uses places your friends actually recommended.

Repo: https://github.com/qcald/final-project (public)

## Run it (about 2 minutes, Python only)

**0. Clone.**

```bash
git clone https://github.com/qcald/final-project.git
cd final-project
```

You need Python 3.11+. The React app is already built into `frontend/dist`, and the backend serves it.

**1. Key.** Put your key in a `.env` file, either in this folder or in the folder one level up
(see `.env.example`):

```
PORTKEY_API_KEY=...
```

**2. Install and start** (from this folder):

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
cd backend
uvicorn main:app --port 8000
```

**3. Open http://localhost:8000** and log in as **maya** (or `maya@example.com`) with password
**friendrecs**.

## Try it

Every demo account (`maya`, `jordan`, `priya`, `sam`, `dana`, `qcald`) uses the test password `friendrecs`.
Maya is friends with Jordan, Priya, and Sam, and has a pending request from Dana. `qcald` is me (Quinn),
with my own real recommendations from New Haven, Stuttgart, and San Francisco. Every new account you
sign up starts out friends with `qcald`, so a brand-new user sees real recs right away.

1. **Ask:** on the **Map** page, choose **Lisbon**, type *"2 days here, I love food and sunsets.
   Where should I stay?"*, and click **Ask**. You get numbered picks on the map with friends' quotes,
   and a note that no friend recommended a place to stay.
2. **Want to go:** click **Want to go** on a pick, then switch the map to **Want to go**.
3. **Import a chat:** open **Import recommendations**, paste `data/sample_chats/cdmx_notes.txt`,
   enter a friend's name, and click **Add to my map**.
4. **Import a Google Maps list:** switch to the **Google Maps list** tab, enter *Lisbon* as the city,
   and choose `data/sample_chats/lisbon_google_maps_list.csv`.
5. **Safety test:** paste `data/sample_chats/injection_test.txt` as a chat. The app flags and ignores
   the line that tries to give the AI orders, and removes the email address.
6. **Share:** on the **Feed** page, post a recommendation. It shows where it was pinned on the map.
   You can edit or delete your own posts. Log in as `jordan` in a private window to see it in their feed.
7. **Friends:** on the **Friends** page, accept Dana's request (Dana's Mexico City recs appear on
   your map), or copy your invite link and open it in a private window to sign up as a new friend.

## Features

- **Accounts and friends:** sign up with a username, email, and password (log in with either),
  add friends by username or invite link, and accept requests. Emails are never shown to other users.
- **Feed:** share a recommendation (place, city, category, rating, note), and edit or delete it later.
  Your friends see it in their feed, on their map, and when they ask for picks.
- **Map:** every place you and your friends recommend, with pins colored by category. Save places to
  a **Want to go** list and filter the map to just those.
- **Import:** paste a group chat or note, or upload a Google Maps saved list (Google Takeout CSV). The
  Intake agent pulls out each recommendation. Imported recs stay private to you, since they're other
  people's words.
- **Ask your friends:** the Answer agent plans from your friends' recs only and quotes who said what.

## How it works

| Agent | Type | Job |
|---|---|---|
| **Intake** | LLM (`gpt-6-luna`) | Turns pasted chats, notes, and Google Maps lists into structured recs: place, city, category, friend, quote, sentiment. |
| **Resolver** | Tool (no LLM) | Geocodes each place with OpenStreetMap (Nominatim) and merges duplicates into the database. Also used for posts, which cost no model tokens. |
| **Answer** | LLM (`gpt-6-luna`) | Answers a trip question using **only** places friends recommended, quoting who said it. |

Every model call's token usage (input, cached input, output) is logged to `output/usage.jsonl`.

### Safety defenses

Each one has a test in `backend/tests/test_safety.py`.

- **Data leaks:** phone numbers and emails are removed before any text reaches the model.
- **Prompt injection:** pasted text is wrapped as data, and lines that try to give the AI orders are
  flagged and ignored.
- **Invented facts:** the Answer agent can only pick places in the user's database; anything else is
  blocked. Sentences that name a place no friend recommended are removed. Friend quotes come from
  the database, not the model.
- **Overspending and loops:** hard caps on pasted text size, model calls per run, and output tokens.
- **Wrong actions and privacy:** every API route needs a login. You only see your own recs, your
  friends' posts, and chats you imported yourself, and you can only edit or delete your own posts.
  Invite codes are signed separately from login tokens, so one can't be used as the other.

Run the tests (from `backend/`, with the virtual environment active):

```bash
python -m pytest tests -v
```

## Benchmark

`scripts/benchmark.py` scores both agents against hand-written right answers (4 sample chats with 23
places, 4 tricky questions) at each reasoning effort, and records tokens and time. It makes about 72
small real model calls and writes `output/benchmark.md` and `output/benchmark.json`.

```bash
python scripts/benchmark.py
```

## Report and slides

`report.html` and `slides.html` are self-contained: screenshots are embedded, and the slides load reveal.js from a CDN with an embedded copy as an offline fallback. They're built
from `docs/report_src.html`, `docs/slides_src.html`, and `docs/screenshots/`:

```bash
python scripts/build_docs.py
```

## Project layout

```
backend/     FastAPI app (main.py), agents, SQLite storage (db.py), auth, safety checks, prompts/, tests/
frontend/    React + Vite app (src/), and its production build (dist/) that the backend serves
data/        sample dataset, sample chats and Google Maps list, geocoding cache
scripts/     benchmark.py, build_docs.py
docs/        report and slide sources, screenshots, user test script
output/      token usage log, benchmark results, test results
```

## Data

- `data/sample_places.json`: the small test dataset in the repo (fictional sample friends).
- `data/friend_recs.db`: the app's SQLite database. If it doesn't exist, the backend creates it on
  startup with the demo accounts and loads the sample places as their posts. It isn't committed.
- To start over with the demo data, stop the backend, delete `data/friend_recs.db`, and start it again.
- To use a different database, set `DB_FILE=/path/to/your.db` before starting the backend.

## Changing the frontend

Only needed if you edit `frontend/src`. You need Node 20+.

```bash
cd frontend
npm install
npm run dev      # live-reloading app at http://localhost:5173 (keep the backend running on 8000)
npm run build    # rebuild frontend/dist, which the backend serves
```
