"""Settings shared by the agents and the app."""

import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_DIR = BACKEND_DIR.parent
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_DIR = PROJECT_DIR / "output"
PROMPTS_DIR = BACKEND_DIR / "prompts"

# .env is looked for in the project folder first, then one level up (where the teaching staff keep keys).
load_dotenv(PROJECT_DIR / ".env")
load_dotenv(PROJECT_DIR.parent / ".env")

# The course key allows only this model.
MODEL = "gpt-6-luna"
PORTKEY_BASE_URL = "https://api.portkey.ai/v1"
# "low", "medium", or "high" (blank = the model's default, medium). scripts/benchmark.py found low just as
# accurate as medium and high on every check, with about a third fewer output tokens, so low is the default.
REASONING_EFFORT = os.environ.get("REASONING_EFFORT", "low")

# The app database. If the file doesn't exist, it's created and loaded with demo users and the sample places.
SAMPLE_PLACES_FILE = DATA_DIR / "sample_places.json"
DB_FILE = Path(os.environ.get("DB_FILE", DATA_DIR / "friend_recs.db"))
GEOCACHE_FILE = DATA_DIR / "geocache.json"
USAGE_LOG = OUTPUT_DIR / "usage.jsonl"

# Every new account starts as friends with this user (if the account exists), so new users see their recs.
DEFAULT_FRIEND = "qcald"

# Guardrails against runaway cost and oversized inputs.
MAX_PASTE_CHARS = 12_000       # longest pasted chat we accept per run
MAX_LLM_CALLS_PER_RUN = 4      # hard stop if an agent loop misbehaves
MAX_OUTPUT_TOKENS = 4_000      # per call
MAX_CANDIDATES = 60            # places sent to the Answer agent per question

# USD per 1M tokens for gpt-6-luna, from third-party pricing listings (eesel.ai, anotherwrapper.com,
# October 2026). Check them against OpenAI's pricing page. Set any to None to hide dollar costs.
PRICE_INPUT = 0.10
PRICE_CACHED_INPUT = 0.01
PRICE_OUTPUT = 0.50

# Nominatim (OpenStreetMap) requires an identifying User-Agent and at most 1 request per second.
GEOCODER_URL = "https://nominatim.openstreetmap.org/search"
GEOCODER_USER_AGENT = "friend-recs-mgt409-class-project/0.1"
