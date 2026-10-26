# Friend Recs: user test script (about 15 minutes per person)

**Goal:** real evidence for the report's Impact section: a before/after timing, a quote, and
screenshots. The rubric caps Impact at half credit without "evidence from a real user."

Aim for **2–3 people**. Friends are fine. Ideally at least one has a real trip coming up.

---

## Before they arrive (10 min, once)

1. Text 3–5 friends: *"Quick favor for my final project: what are your top 3–5 spots in [city you've
   been to]? Restaurants, bars, views, anything. One line each on why."* Save the replies as they come.
2. Start the app (`uvicorn main:app --port 8000` from `backend/`) and log in as yourself.
3. Paste those real replies into **Import recommendations** (one friend per paste), and/or have
   friends who are with you post their own recs on the **Feed**.
4. Find a real group chat or notes app thread where someone once asked for or gave travel recs.
   That's the "before" for Task A.

## With each person

Say: *"I'm testing an app, not you. Think out loud. There are no wrong answers."* Ask whether you can
quote them by first name in a class report, and screenshot their session.

### Task A: the old way (time it)

> "You're going to [city] next month. Using only your texts, group chats, or notes, find **3 places
> friends recommended** and who recommended each. Go."

- Start a stopwatch when they start scrolling. Stop when they've named 3 places plus who said each.
- Note how many places they found, and whether they remembered who said what.
- Cap it at 5 minutes. If they give up, record "gave up at 5:00" (that's evidence too).

### Task B: with Friend Recs (time it)

> "Now do the same thing in this app."

- Log them in (or use your account). Map page → choose the city → ask
  *"3 places I shouldn't miss"* (or their own question) → **Ask**.
- Time from opening the Map page to when they can name 3 places plus who said each.

### Task C: share a rec (time it)

> "Post one place you'd recommend to a friend."

- Feed page → Share a recommendation. Time from opening the form to clicking **Post to friends**.

### Three questions (write down their exact words)

1. "How do you usually find out where to go on a trip? What's annoying about it?"
2. "Would you trust these picks more or less than Google or TripAdvisor? Why?"
3. "What would make you actually use this before your next trip?"

Then ask: *"If you had to describe this to a friend in one sentence, what would you say?"*
That sentence is often the best quote for the report.

---

## Results table (fill in)

| Person (first name) | Trip / city | Task A: old way (m:ss) | Places found (A) | Remembered who said it? (A) | Task B: app (m:ss) | Task C: post (m:ss) | Best quote |
|---|---|---|---|---|---|---|---|
|  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |
|  |  |  |  |  |  |  |  |

## Screenshots to take

- [ ] Someone mid-scroll in a group chat during Task A (crop out other people's messages)
- [ ] Their Friend Recs answer with numbered pins
- [ ] The "How this answer was made" panel for that answer
- [ ] Their post appearing in a friend's feed

## How this goes into the report

- **Impact:** "Finding 3 friend recommendations took a median of X:XX by scrolling chats vs. Y:YY in
  Friend Recs (N people), and in the old way, Z of N couldn't remember who recommended what."
- **Motivation:** quotes from question 1.
- **What's new:** quotes from question 2 (trust in friends vs. strangers' reviews).
- **Limits and next steps:** whatever confused them or what they asked for in question 3.

Report what actually happened, even if the app was slower for someone. Honest numbers with a short
explanation score better than numbers that look made up.
