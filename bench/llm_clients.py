"""Authenticated Grok and OpenRouter chat-completion clients."""

import json
import logging
import os
from pathlib import Path
import sqlite3
import subprocess
import time
from urllib import error, request

logger = logging.getLogger(__name__)

GROK_URL = "https://cli-chat-proxy.grok.com/v1/chat/completions"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
CREDENTIAL_DB = Path.home() / ".omp/agent/agent.db"


class LlmError(RuntimeError):
    """An HTTP, timeout, or completion-body failure."""


def _grok_access() -> str:
    def load() -> dict:
        with sqlite3.connect(f"file:{CREDENTIAL_DB}?mode=ro", uri=True) as db:
            row = db.execute(
                "SELECT data FROM auth_credentials WHERE provider = ? AND credential_type = ? "
                "AND disabled_cause IS NULL ORDER BY updated_at DESC LIMIT 1",
                ("xai-oauth", "oauth"),
            ).fetchone()
        if row is None:
            raise LlmError("No enabled xai-oauth credential")
        return json.loads(row[0])

    credential = load()
    if int(credential.get("expires", 0)) <= int(time.time() * 1000):
        refresh = subprocess.run(
            ["omp", "-p", "Reply ok", "--model", "xai-oauth/grok-4.6", "--no-session"],
            capture_output=True, text=True, timeout=180, check=False,
        )
        if refresh.returncode:
            raise LlmError(f"omp OAuth refresh failed with exit code {refresh.returncode}")
        if int(credential.get("expires", 0)) <= int(time.time() * 1000):
            raise LlmError("xai-oauth credential is still expired after refresh")
    access = credential.get("access")
    if not isinstance(access, str) or not access:
        raise LlmError("xai-oauth access token is missing")
    return access


def _chat(url: str, headers: dict, body: dict, log_path: Path | None) -> dict:
    encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
    safe_headers = {key: value for key, value in headers.items() if key.lower() != "authorization"}
    req = request.Request(url, data=encoded, headers=headers, method="POST")
    try:
        with request.urlopen(req, timeout=600) as response:
            status = response.status
            raw_bytes = response.read()
    except error.HTTPError as exc:
        logger.warning("LLM HTTP failure: %s %s", url, exc.code)
        raise LlmError(f"LLM HTTP {exc.code} at {url}") from exc
    except (error.URLError, TimeoutError) as exc:
        logger.exception("LLM transport failure at %s", url)
        raise LlmError(f"LLM transport failure at {url}: {exc}") from exc
    if status >= 400:
        raise LlmError(f"LLM HTTP {status} at {url}")
    try:
        raw = json.loads(raw_bytes)
    except (ValueError, UnicodeDecodeError) as exc:
        logger.exception("LLM response JSON decode failure")
        raise LlmError("LLM response was not JSON") from exc
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps({"url": url, "request": body, "request_headers": safe_headers,
                                        "response": raw}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if raw.get("error"):
        raise LlmError(f"LLM returned error in HTTP 200 body: {raw['error']}")
    choices = raw.get("choices") or []
    if not choices:
        raise LlmError("LLM response has no choices")
    content = choices[0].get("message", {}).get("content")
    if not isinstance(content, str):
        raise LlmError("LLM response has no text content")
    return {"content": content, "usage": raw.get("usage") or {}, "model": raw.get("model") or body["model"], "raw": raw}


def grok_chat(messages: list[dict], *, model: str = "grok-4.6", reasoning_effort: str | None = None,
              max_tokens: int | None = None, response_format: dict | None = None,
              log_path: Path | None = None) -> dict:
    """Call the xAI OAuth chat proxy."""
    body = {"model": model, "messages": messages}
    if max_tokens is not None:
        body["max_tokens"] = max_tokens
    if reasoning_effort is not None:
        body["reasoning_effort"] = reasoning_effort
    if response_format is not None:
        body["response_format"] = response_format
    access = _grok_access()
    return _chat(GROK_URL, {
        "Authorization": f"Bearer {access}",
        "Content-Type": "application/json", "x-grok-client-version": "1.0.13",
        "x-grok-client-identifier": "grok-shell", "User-Agent": "xai-grok-cli",
    }, body, log_path)


def openrouter_chat(model: str, messages: list[dict], *, max_tokens: int | None = None,
                    response_format: dict | None = None, reasoning_effort: str | None = None,
                    log_path: Path | None = None) -> dict:
    """Call the OpenRouter chat-completion endpoint."""
    token = os.environ.get("OPENROUTER_API_KEY")
    if not token:
        raise LlmError("OPENROUTER_API_KEY is not set")
    body = {"model": model, "messages": messages}
    if max_tokens is not None:
        body["max_tokens"] = max_tokens
    if response_format is not None:
        body["response_format"] = response_format
    if reasoning_effort is not None:
        body["reasoning"] = {"effort": reasoning_effort}
    return _chat(OPENROUTER_URL, {
        "Authorization": f"Bearer {token}", "Content-Type": "application/json",
    }, body, log_path)
