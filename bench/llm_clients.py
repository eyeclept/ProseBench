"""Authenticated Grok (xAI OAuth), ChatGPT-subscription (codex OAuth), and OpenRouter chat clients.

OAuth tokens come read-only from omp's credential store; nothing here writes it or prints a token.
"""

import json
import logging
from pathlib import Path
import sqlite3
import subprocess
import time
import uuid
from urllib import error, request

logger = logging.getLogger(__name__)

GROK_URL = "https://cli-chat-proxy.grok.com/v1/chat/completions"
CREDENTIAL_DB = Path.home() / ".omp/agent/agent.db"
TRANSIENT_RETRY_S = 30
CHATGPT_URL = "https://chatgpt.com/backend-api/codex/responses"


class LlmError(RuntimeError):
    """An HTTP, timeout, or completion-body failure."""


class LlmQuotaError(LlmError):
    """The subscription usage window is exhausted; retrying before the reset only burns calls."""


def _oauth_credential(provider: str, refresh_model: str) -> dict:
    """Read an omp OAuth credential read-only; if expired, let omp refresh it once and reload."""
    def load() -> dict:
        with sqlite3.connect(f"file:{CREDENTIAL_DB}?mode=ro", uri=True) as db:
            row = db.execute(
                "SELECT data FROM auth_credentials WHERE provider = ? AND credential_type = ? "
                "AND disabled_cause IS NULL ORDER BY updated_at DESC LIMIT 1",
                (provider, "oauth"),
            ).fetchone()
        if row is None:
            raise LlmError(f"No enabled {provider} credential")
        return json.loads(row[0])

    credential = load()
    if int(credential.get("expires", 0)) <= int(time.time() * 1000):
        refresh = subprocess.run(
            ["omp", "-p", "Reply ok", "--model", refresh_model, "--no-session"],
            capture_output=True, text=True, timeout=180, check=False,
        )
        if refresh.returncode:
            raise LlmError(f"omp OAuth refresh for {provider} failed with exit code {refresh.returncode}")
        credential = load()
        if int(credential.get("expires", 0)) <= int(time.time() * 1000):
            raise LlmError(f"{provider} credential is still expired after refresh")
    if not isinstance(credential.get("access"), str) or not credential["access"]:
        raise LlmError(f"{provider} access token is missing")
    return credential


def _grok_access() -> str:
    return _oauth_credential("xai-oauth", "xai-oauth/grok-4.6")["access"]


def _chat(url: str, headers: dict, body: dict, log_path: Path | None) -> dict:
    encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
    safe_headers = {key: value for key, value in headers.items() if key.lower() != "authorization"}
    for attempt in (1, 2):
        req = request.Request(url, data=encoded, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=600) as response:
                status = response.status
                raw_bytes = response.read()
            break
        except error.HTTPError as exc:
            # One delayed retry for transient upstream failures (the Grok proxy returned sporadic HTTP 500s).
            if attempt == 1 and (exc.code >= 500 or exc.code == 429):
                logger.warning("LLM HTTP %s at %s; retrying once in %ss", exc.code, url, TRANSIENT_RETRY_S)
                time.sleep(TRANSIENT_RETRY_S)
                continue
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


def chatgpt_chat(messages: list[dict], *, model: str = "gpt-6.1-sol", reasoning_effort: str | None = None,
                 response_format: dict | None = None, log_path: Path | None = None) -> dict:
    """Call GPT through the owner's ChatGPT subscription (omp `openai-codex` OAuth, Responses API).

    Chat-style messages map to Responses input: system text becomes `instructions`. A chat-style
    `response_format` (json_schema or json_object) maps to `text.format`. The backend streams SSE; this
    collects the final `response.completed` event. Subscription calls report cost_usd 0.
    """
    credential = _oauth_credential("openai-codex", "openai-codex/gpt-6.1-sol")
    system = "\n\n".join(m["content"] for m in messages if m["role"] == "system")
    items = [{"role": m["role"], "content": [{"type": "input_text" if m["role"] == "user" else "output_text",
                                              "text": m["content"]}]}
             for m in messages if m["role"] != "system"]
    body = {"model": model, "instructions": system or "Follow the user's instructions.", "input": items,
            "stream": True, "store": False}
    if reasoning_effort is not None:
        body["reasoning"] = {"effort": reasoning_effort}
    if response_format is not None:
        if response_format.get("type") == "json_schema":
            spec = response_format["json_schema"]
            body["text"] = {"format": {"type": "json_schema", "name": spec["name"],
                                       "strict": spec.get("strict", False), "schema": spec["schema"]}}
        else:
            body["text"] = {"format": {"type": response_format["type"]}}
    headers = {"Authorization": f"Bearer {credential['access']}", "chatgpt-account-id": credential["accountId"],
               "OpenAI-Beta": "responses=experimental", "originator": "codex_cli_rs",
               "session_id": str(uuid.uuid4()), "Content-Type": "application/json", "Accept": "text/event-stream"}
    encoded = json.dumps(body, ensure_ascii=False).encode("utf-8")
    for attempt in (1, 2):
        req = request.Request(CHATGPT_URL, data=encoded, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=600) as response:
                stream = response.read().decode("utf-8")
            break
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", "replace")[:500]
            if exc.code == 429 and "limit_reached" in detail:
                logger.warning("ChatGPT usage limit reached: %s", detail)
                raise LlmQuotaError(f"ChatGPT usage limit reached: {detail}") from exc
            if attempt == 1 and (exc.code >= 500 or exc.code == 429):
                logger.warning("ChatGPT HTTP %s; retrying once in %ss: %s", exc.code, TRANSIENT_RETRY_S, detail)
                time.sleep(TRANSIENT_RETRY_S)
                continue
            logger.warning("ChatGPT HTTP failure %s: %s", exc.code, detail)
            raise LlmError(f"ChatGPT HTTP {exc.code}: {detail}") from exc
        except (error.URLError, TimeoutError) as exc:
            logger.exception("ChatGPT transport failure")
            raise LlmError(f"ChatGPT transport failure: {exc}") from exc
    final = None
    items_done = []
    for line in stream.splitlines():
        if not line.startswith("data: "):
            continue
        try:
            event = json.loads(line[6:])
        except json.JSONDecodeError:
            logger.warning("Skipping non-JSON SSE line from ChatGPT")
            continue
        if event.get("type") in ("response.failed", "error"):
            raise LlmError(f"ChatGPT returned an error event: {json.dumps(event)[:300]}")
        if event.get("type") == "response.output_item.done":
            items_done.append(event["item"])
        if event.get("type") == "response.completed":
            final = event["response"]
    if final is None:
        raise LlmError("ChatGPT stream ended without response.completed")
    # The completed event sometimes carries an empty output list; the items always arrive as output_item.done.
    output = final.get("output") or items_done
    text = "".join(part.get("text", "") for item in output if item.get("type") == "message"
                   for part in item.get("content", []) if part.get("type") == "output_text")
    if not text:
        raise LlmError("ChatGPT response completed with no output text")
    if log_path is not None:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        log_path.write_text(json.dumps({"url": CHATGPT_URL, "request": body, "response": final},
                                       ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    usage = dict(final.get("usage") or {}, cost=0.0)
    return {"content": text, "usage": usage, "model": final.get("model") or model, "raw": final}
