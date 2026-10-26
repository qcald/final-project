"""One place for model calls: the Portkey client, JSON output, and per-run token logging."""

import json
import os
import time
import uuid
from datetime import datetime, timezone

from openai import OpenAI

import config

_client = None


def client() -> OpenAI:
    global _client
    if _client is None:
        key = os.environ.get("PORTKEY_API_KEY")
        if not key:
            raise RuntimeError("PORTKEY_API_KEY is not set. Put it in .env here or one folder up.")
        _client = OpenAI(api_key=key, base_url=config.PORTKEY_BASE_URL,
                         default_headers={"x-portkey-api-key": key})
    return _client


def cost_usd(input_tokens: int, cached: int, output_tokens: int) -> float | None:
    if None in (config.PRICE_INPUT, config.PRICE_CACHED_INPUT, config.PRICE_OUTPUT):
        return None
    return ((input_tokens - cached) * config.PRICE_INPUT
            + cached * config.PRICE_CACHED_INPUT
            + output_tokens * config.PRICE_OUTPUT) / 1_000_000


class Run:
    """One user action (adding recs, or asking a question). Tracks every model call it makes, and
    a step-by-step trace of everything that happened, which the app shows under each result."""

    def __init__(self, kind: str):
        self.id = uuid.uuid4().hex[:10]
        self.kind = kind
        self.calls = []
        self.trace = []
        self._start = time.time()

    def step(self, agent: str, kind: str, title: str, detail: str = "") -> None:
        """Record one step. kind is "check" (code safety check), "tool", "model", or "result"."""
        self.trace.append({"agent": agent, "kind": kind, "title": title, "detail": detail,
                           "at_ms": round((time.time() - self._start) * 1000)})

    def call_json(self, agent: str, system: str, user: str, schema: dict) -> dict:
        if len(self.calls) >= config.MAX_LLM_CALLS_PER_RUN:
            raise RuntimeError(f"Stopped: run hit the limit of {config.MAX_LLM_CALLS_PER_RUN} model calls.")
        start = time.time()
        resp = client().responses.create(
            model=config.MODEL,
            instructions=system,  # static prompt first, so repeat calls can hit the prompt cache
            input=user,
            max_output_tokens=config.MAX_OUTPUT_TOKENS,
            **({"reasoning": {"effort": config.REASONING_EFFORT}} if config.REASONING_EFFORT else {}),
            text={"format": {"type": "json_schema", "name": agent, "strict": True, "schema": schema}},
        )
        u = resp.usage
        cached = getattr(u.input_tokens_details, "cached_tokens", 0) or 0
        record = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "run_id": self.id, "run_kind": self.kind, "agent": agent, "model": config.MODEL,
            "reasoning_effort": config.REASONING_EFFORT or "default",
            "input_tokens": u.input_tokens, "cached_input_tokens": cached,
            "output_tokens": u.output_tokens,
            "reasoning_tokens": getattr(u.output_tokens_details, "reasoning_tokens", 0) or 0,
            "seconds": round(time.time() - start, 2),
        }
        record["cost_usd"] = cost_usd(u.input_tokens, cached, u.output_tokens)
        self.calls.append(record)
        self.step(agent, "model", f"{config.MODEL} call",
                  f"{u.input_tokens:,} input tokens ({cached:,} cached), {u.output_tokens:,} output tokens, "
                  f"{record['seconds']:.1f}s")
        config.OUTPUT_DIR.mkdir(exist_ok=True)
        with open(config.USAGE_LOG, "a") as f:
            f.write(json.dumps(record) + "\n")
        return json.loads(resp.output_text)

    def totals(self) -> dict:
        t = {k: sum(c[k] for c in self.calls)
             for k in ("input_tokens", "cached_input_tokens", "output_tokens", "seconds")}
        t["calls"] = len(self.calls)
        t["cost_usd"] = cost_usd(t["input_tokens"], t["cached_input_tokens"], t["output_tokens"])
        return t
