"""Tests run against a throwaway database, and never call the real model."""

import os
import sys
import tempfile
from pathlib import Path

# Must be set before config is imported anywhere
os.environ["DB_FILE"] = str(Path(tempfile.mkdtemp()) / "test.db")
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

import db  # noqa: E402
import main  # noqa: E402


@pytest.fixture()
def client():
    """A fresh demo database for each test."""
    Path(os.environ["DB_FILE"]).unlink(missing_ok=True)
    db.init_db()
    return TestClient(main.app)


def login(client, username: str) -> dict:
    res = client.post("/api/auth/login", json={"username": username, "password": db.DEMO_PASSWORD})
    return {"Authorization": f"Bearer {res.json()['token']}"}


class FakeRun:
    """Stands in for llm.Run: returns a canned model reply and records what was sent."""

    def __init__(self, reply: dict):
        self.reply = reply
        self.sent = []
        self.trace = []

    def step(self, agent, kind, title, detail=""):
        self.trace.append({"agent": agent, "kind": kind, "title": title, "detail": detail, "at_ms": 0})

    def call_json(self, agent, system, user, schema):
        self.sent.append(user)
        return self.reply

    def totals(self):
        return {"calls": len(self.sent), "input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 0,
                "seconds": 0.0, "cost_usd": None}
