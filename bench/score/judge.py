"""Batch uncertain instance verdicts through Grok 4.6 with disk caching."""

import hashlib
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)
PROMPT = Path(__file__).with_name("judge_prompt.md")
JUDGE_MODEL = "grok-4.6"
JUDGE_EFFORT = "medium"


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def cache_key(run_id: str, item: dict, context: list[str]) -> str:
    """Key on the full item the judge sees, not just its instance_id: an answer-key edit that keeps the ID but
    changes the target, polarity, or action must miss the cache instead of reusing a stale verdict."""
    return _sha(json.dumps([run_id, item, *context], sort_keys=True, ensure_ascii=True, separators=(",", ":")))


def judge_run(run_id: str, original: str, revised: str,
              items: list[dict], cache_dir: Path) -> dict[str, dict]:
    """Request one structured response per run for all missing cache entries.

    Callers pass a model-qualified run_id (run stems repeat across models). The cache key also covers the
    judge model and effort, so changing either re-judges instead of mixing settings.
    """
    prompt = PROMPT.read_text(encoding="utf-8")
    context = [_sha(prompt), JUDGE_MODEL, JUDGE_EFFORT]
    cache_dir.mkdir(parents=True, exist_ok=True)
    verdicts = {}
    pending = []
    for item in items:
        key = cache_key(run_id, item, context)
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

    logger.info("Judging %d items for %s", len(pending), run_id)
    request = {"before": original, "after": revised,
               "items": [item for item, _ in pending]}
    expected = {item["instance_id"] for item, _ in pending}
    # The judge is measurement infrastructure, not a tested model: an empty or malformed reply gets one
    # resend before the run fails.
    for attempt in (1, 2):
        response = grok_chat([{"role": "system", "content": prompt},
                              {"role": "user", "content": json.dumps(request, ensure_ascii=True)}],
                             model=JUDGE_MODEL, reasoning_effort=JUDGE_EFFORT,
                             response_format={"type": "json_object"})
        try:
            payload = json.loads(response["content"])
            entries = payload["verdicts"]
            actual = [entry["instance_id"] for entry in entries]
            if len(actual) != len(expected) or set(actual) != expected:
                raise ValueError("Judge returned missing, duplicate, or extra instance IDs")
            if any(entry.get("verdict") not in ("correct", "incorrect") or
                   not isinstance(entry.get("reason"), str) for entry in entries):
                raise ValueError("Judge returned invalid verdict or reason")
            break
        except (ValueError, KeyError, TypeError):
            if attempt == 2:
                logger.exception("Invalid Grok judge response for %s after a resend", run_id)
                raise
            logger.warning("Invalid Grok judge response for %s; resending once", run_id)
    # Store the model the endpoint reports, so a silent fallback near a usage limit is detectable later.
    by_id = {entry["instance_id"]: dict(entry, model=response.get("model", "")) for entry in entries}
    for item, path in pending:
        entry = by_id[item["instance_id"]]
        path.write_text(json.dumps(entry, ensure_ascii=True) + "\n", encoding="utf-8")
        verdicts[item["instance_id"]] = entry
    return verdicts
