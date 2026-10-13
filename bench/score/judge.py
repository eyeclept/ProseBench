"""Batch uncertain instance verdicts through Grok 4.6 with disk caching."""

import hashlib
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
PROMPT = Path(__file__).with_name("judge_prompt.md")


def judge_run(run_id: str, original: str, revised: str,
              items: list[dict], cache_dir: Path) -> dict[str, dict]:
    """Request one structured response per run for all missing cache entries."""
    prompt = PROMPT.read_text(encoding="utf-8")
    prompt_sha = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    cache_dir.mkdir(parents=True, exist_ok=True)
    verdicts = {}
    pending = []
    for item in items:
        key = hashlib.sha256(json.dumps([run_id, item["instance_id"], prompt_sha],
                                        separators=(",", ":")).encode("utf-8")).hexdigest()
        path = cache_dir / f"{key}.json"
        if path.exists():
            value = json.loads(path.read_text(encoding="utf-8"))
            if value.get("instance_id") != item["instance_id"] or value.get("verdict") not in ("correct", "incorrect"):
                raise ValueError(f"Invalid judge cache entry: {path}")
            verdicts[item["instance_id"]] = value
        else:
            pending.append((item, path))
    if not pending:
        return verdicts
    # Lazy import keeps deterministic scoring and unit tests independent of credentials.
    from bench.llm_clients import grok_chat

    request = {"before": original, "after": revised,
               "items": [item for item, _ in pending]}
    response = grok_chat([{"role": "system", "content": prompt},
                          {"role": "user", "content": json.dumps(request, ensure_ascii=True)}],
                         model="grok-4.6", response_format={"type": "json_object"})
    try:
        payload = json.loads(response["content"])
        entries = payload["verdicts"]
        expected = {item["instance_id"] for item, _ in pending}
        actual = [entry["instance_id"] for entry in entries]
        if len(actual) != len(expected) or set(actual) != expected:
            raise ValueError("Judge returned missing, duplicate, or extra instance IDs")
        if any(entry.get("verdict") not in ("correct", "incorrect") or
               not isinstance(entry.get("reason"), str) for entry in entries):
            raise ValueError("Judge returned invalid verdict or reason")
    except (ValueError, KeyError, TypeError):
        logger.exception("Invalid Grok judge response")
        raise
    by_id = {entry["instance_id"]: entry for entry in entries}
    for item, path in pending:
        entry = by_id[item["instance_id"]]
        path.write_text(json.dumps(entry, ensure_ascii=True) + "\n", encoding="utf-8")
        verdicts[item["instance_id"]] = entry
    return verdicts
