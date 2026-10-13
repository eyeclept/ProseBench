"""Extract assistant output and accounting from omp JSON event streams."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class Events:
    output_text: str
    usage: dict[str, int]
    cost_usd: float
    tool_calls: list[dict]
    error: str | None


def _number(value: object) -> int:
    return int(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0


def _assistant_text(message: dict) -> str:
    content = message.get("content", [])
    if isinstance(content, str):
        return content.strip()
    if not isinstance(content, list):
        return ""
    return "".join(part.get("text", "") for part in content if isinstance(part, dict) and part.get("type") == "text").strip()


def parse_events(raw: str) -> Events:
    events = []
    errors = []
    for line_number, line in enumerate(raw.splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            logger.warning("Invalid omp event line %d: %s", line_number, exc)
            errors.append(f"invalid omp JSONL line {line_number}: {exc}")
            continue
        if not isinstance(event, dict):
            errors.append(f"omp event line {line_number} is not an object")
            continue
        events.append(event)

    assistants = []
    tool_calls = []
    for event in events:
        kind = event.get("type")
        if kind == "tool_execution_start":
            tool_calls.append({"name": event.get("toolName"), "arguments": event.get("args")})
        if kind in ("error", "agent_error", "turn_error"):
            detail = event.get("error") or event.get("message") or kind
            errors.append(str(detail))
        if kind == "agent_end":
            messages = event.get("messages") or []
            assistants = [m for m in messages if isinstance(m, dict) and m.get("role") == "assistant"]

    usage = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "reasoning": 0}
    cost_usd = 0.0
    for message in assistants:
        source_usage = message.get("usage") or {}
        if not isinstance(source_usage, dict):
            continue
        usage["input"] += _number(source_usage.get("input", source_usage.get("inputTokens")))
        usage["output"] += _number(source_usage.get("output", source_usage.get("outputTokens")))
        usage["cache_read"] += _number(source_usage.get("cacheRead", source_usage.get("cache_read")))
        usage["cache_write"] += _number(source_usage.get("cacheWrite", source_usage.get("cache_write")))
        usage["reasoning"] += _number(source_usage.get("reasoning", source_usage.get("reasoningTokens", (source_usage.get("outputTokenDetails") or {}).get("reasoningTokens"))))
        message_cost = source_usage.get("cost") or {}
        if isinstance(message_cost, dict):
            message_cost = message_cost.get("total", 0)
        cost_usd += float(message_cost or 0)
    return Events(_assistant_text(assistants[-1]) if assistants else "", usage, cost_usd, tool_calls, "; ".join(errors) or None)


def parse_edits(text: str) -> tuple[list[dict] | None, str | None, list]:
    """Find the first JSON object, ignoring surrounding prose and Markdown fences.

    Returns (edits, parse_error, malformed). `original` (str) and `replacement` (str or null) are required per
    edit; `reason` is metadata and may be missing. Edits lacking a required field go to `malformed` and are not
    applied; the run still scores its well-formed edits. parse_error is set only when no usable edits list exists.
    """
    cleaned = re.sub(r"(?m)^\s*```(?:json)?\s*$", "", text, flags=re.IGNORECASE)
    decoder = json.JSONDecoder()
    for index, char in enumerate(cleaned):
        if char != "{":
            continue
        try:
            value, _ = decoder.raw_decode(cleaned, index)
        except json.JSONDecodeError as exc:
            logger.warning("Invalid output JSON object: %s", exc)
            return None, f"invalid output JSON: {exc}", []
        if not isinstance(value, dict):
            return None, "output JSON is not an object", []
        edits = value.get("edits")
        if not isinstance(edits, list):
            return None, "output JSON must contain an edits list", []
        good, malformed = [], []
        for edit in edits:
            if (isinstance(edit, dict) and isinstance(edit.get("original"), str) and "replacement" in edit
                    and (edit["replacement"] is None or isinstance(edit["replacement"], str))):
                good.append(edit)
            else:
                malformed.append(edit)
        if malformed:
            logger.warning("%d malformed edits not applied", len(malformed))
        return good, None, malformed
    return None, "no JSON object in final assistant text", []
