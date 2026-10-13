"""Smoke-test the isolated omp harness and record model thinking levels."""

import argparse
import json
import logging
from pathlib import Path
import re
import sqlite3
import subprocess
import sys
import tempfile

import yaml

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent.parent
CONTAINER = ROOT / "container"
ROSTER = ROOT / "bench" / "roster.yml"
PROMPT = "Reply with the single word: ok\n"
LEVELS = ("off", "minimal", "low")


def claude_authenticated() -> bool:
    """Check the isolated credential store without reading its secret data."""
    database = Path.home() / ".local/share/prosebench/omp-state/agent.db"
    if not database.exists():
        return False
    try:
        with sqlite3.connect(f"file:{database}?mode=ro", uri=True) as conn:
            return conn.execute(
                "SELECT 1 FROM auth_credentials WHERE provider = ? "
                "AND credential_type = ? AND disabled_cause IS NULL LIMIT 1",
                ("anthropic", "oauth"),
            ).fetchone() is not None
    except sqlite3.Error:
        logger.exception("Cannot read isolated Anthropic auth metadata")
        raise


def run_one(model: str, level: str, prompt: Path, events: Path) -> dict:
    """Run one prompt, then summarize only the last assistant message."""
    with events.open("w", encoding="utf-8") as stream:
        proc = subprocess.run(
            [str(CONTAINER / "omp-run.sh"), "--model", model, "--thinking", level,
             "--prompt-file", str(prompt)],
            cwd=ROOT, stdout=stream, stderr=subprocess.PIPE, text=True,
            timeout=240, check=False,
        )
    assistant = []
    with events.open(encoding="utf-8") as stream:
        for line in stream:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                logger.exception("Invalid JSONL event from %s", model)
                raise
            if event.get("type") == "message_end" and event.get("message", {}).get("role") == "assistant":
                assistant.append(event["message"])
    message = assistant[-1] if assistant else {}
    usage = message.get("usage", {})
    cost = usage.get("cost", {}).get("total", 0)
    return {
        "exit": proc.returncode,
        "text": "".join(part.get("text", "") for part in message.get("content", []) if part.get("type") == "text"),
        "prompt_tokens": sum(usage.get(key, 0) for key in ("input", "cacheRead", "cacheWrite")),
        "reasoning_tokens": usage.get("reasoning", 0),
        "cost": float(cost),
        "stop": message.get("stopReason", "no-assistant-event"),
        "error": message.get("errorMessage") or proc.stderr.strip(),
        "error_status": message.get("errorStatus"),
    }


def _keys(spec: str, scored: dict) -> list[str]:
    if spec == "all":
        return list(scored)
    items = spec.split(",")
    if not items or any(item not in scored for item in items) or len(set(items)) != len(items):
        raise ValueError(
            f"Invalid models: {spec}; choose comma-separated values from {', '.join(scored)} or all"
        )
    return items


def _probe_levels(key: str) -> tuple[str, ...]:
    if key.endswith("_high"):
        return ("high",)
    return LEVELS


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", default="all", help="comma-separated scored model keys, or all")
    args = parser.parse_args(argv)
    roster = yaml.safe_load(ROSTER.read_text(encoding="utf-8"))
    scored = roster["scored"]
    records = []
    costs = 0.0
    auth = claude_authenticated()
    with tempfile.TemporaryDirectory(prefix=".smoke-", dir=CONTAINER) as scratch:
        prompt = Path(scratch) / "prompt.md"
        prompt.write_text(PROMPT, encoding="ascii")
        for key in _keys(args.models, scored):
            spec = scored[key]
            model = spec["model"]
            if model.startswith("anthropic/") and not auth:
                records.append((key, "needs-login", "unverified", None))
                continue
            result = None
            for level in _probe_levels(key):
                result = run_one(model, level, prompt, Path(scratch) / "events.jsonl")
                costs += result["cost"]
                if (result["stop"] == "stop" and result["exit"] == 0
                        and re.search(r"\bok\b", result["text"], flags=re.IGNORECASE)):
                    records.append((key, "pass", level, result))
                    break
                status = result["error_status"]
                error = str(result["error"])
                if status == 429:
                    records.append((key, "rate-limited", "unverified", result))
                    break
                if status == 400 and any(phrase in error.lower() for phrase in ("thinking", "reasoning", "effort")):
                    continue
                logger.warning("Smoke failed for %s at %s: exit=%s status=%s text=%r error=%s",
                               key, level, result["exit"], status, result["text"], error)
                records.append((key, "response-mismatch" if result["stop"] == "stop" else "error",
                                "unverified", result))
                break
            else:
                records.append((key, "thinking-rejected", "unverified", result))

    source = ROSTER.read_text(encoding="utf-8")
    for key, status, level, _ in records:
        if status != "pass":
            continue
        pattern = rf"(^  {re.escape(key)}:\s*\{{[^\n]*?thinking: )[^,}}]+"
        # Quote the level: YAML 1.1 reads a bare off/on as a boolean.
        source, count = re.subn(pattern, rf'\g<1>"{level}"', source, count=1, flags=re.MULTILINE)
        if count != 1:
            raise ValueError(f"Roster row missing for {key}")
    ROSTER.write_text(source, encoding="utf-8")
    rows = [
        "# Smoke results", "", "Prompt: `Reply with the single word: ok`.",
        "Prompt tokens include cached input and cache-write tokens. All costs are US dollars.", "",
        "| Model | Status | Exit | Final text | Prompt tokens | Reasoning tokens | Cost (USD) | Minimum thinking |",
        "| --- | --- | ---: | --- | ---: | ---: | ---: | --- |",
    ]
    for key, status, level, result in records:
        if result is None:
            columns = (key, status, "-", "-", "-", "-", "-", level)
        else:
            text = result["text"].replace("|", "\\|").replace("\n", " ")[:90]
            columns = (key, status, str(result["exit"]), text or "-", str(result["prompt_tokens"]),
                       str(result["reasoning_tokens"]), f"{result['cost']:.8f}", level)
        rows.append("| " + " | ".join(columns) + " |")
    rows.extend(("", f"Total model-reported cost: ${costs:.8f}.", ""))
    for key, status, level, result in records:
        if result and status != "pass":
            rows.append(f"- `{key}` at `{level}`: {result['error'] or result['text'] or result['stop']}")
    rows.append("")
    (CONTAINER / "smoke_results.md").write_text("\n".join(rows), encoding="ascii")
    print("\n".join(rows))
    return 0 if all(status in ("pass", "needs-login", "endpoint-busy") for _, status, _, _ in records) else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, ValueError, subprocess.TimeoutExpired):
        logger.exception("Smoke run aborted")
        raise
