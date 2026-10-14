"""Plan and execute guarded ProseBench runs through the pinned omp wrapper."""

from __future__ import annotations

import argparse
import json
import re
import logging
import os
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

import yaml

from bench.runner.omp_events import parse_edits, parse_events
from bench.runner.prompt import assemble

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[2]
# Endpoint-busy backoff (seconds). OpenRouter 429s hit Mistral Small 4.
BUSY_WAITS = (120, 300)
ENDPOINT_BUSY = re.compile(r'"errorStatus"\s*:\s*(?:429|503)\b')
# Run cap in seconds, passed to the wrapper as omp --max-time and recorded per run as max_time_s.
# Records written before the field existed ran at 600 s. Owner policy: 1200 s, then 2400 s for runs that hit 1200 s.
MAX_TIME_S = 1200
LEGACY_MAX_TIME_S = 600
DEADLINE = re.compile(r"Deadline exceeded")


def _last_error_message(stdout: str) -> str:
    """Last omp errorMessage in the event stream, for runs whose stderr is empty (provider errors, deadlines)."""
    for line in reversed(stdout.splitlines()):
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            logger.warning("Skipping non-JSON event line while extracting error message")
            continue
        message = event.get("message") if isinstance(event, dict) else None
        if isinstance(message, dict) and message.get("errorMessage"):
            return str(message["errorMessage"])
    return ""


def _selection(spec: str, allowed: tuple[str, ...], name: str) -> list[str]:
    if spec == "all":
        return list(allowed)
    items = spec.split(",")
    if not items or any(item not in allowed for item in items) or len(set(items)) != len(items):
        raise ValueError(f"Invalid {name}: {spec}; choose comma-separated values from {', '.join(allowed)} or all")
    return items


def _pin(root: Path) -> dict:
    pin = {}
    path = root / "container" / "pin.env"
    if not path.exists():
        return pin
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("PROSEBENCH_OMP_VERSION=") or line.startswith("PROSEBENCH_IMAGE_DIGEST="):
            key, value = line.split("=", 1)
            pin[key] = value.strip().strip('"\'')
    return pin


def _atomic_write(path: Path, data: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, prefix="." + path.name + ".", delete=False) as stream:
            tmp_path = Path(stream.name)
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        tmp_path.replace(path)
    finally:
        if tmp_path is not None:
            tmp_path.unlink(missing_ok=True)


def _invoke(root: Path, wrapper: str, model: str, thinking: str, user_prompt: str,
            max_time: int) -> tuple[subprocess.CompletedProcess[str], float]:
    with tempfile.TemporaryDirectory(prefix=".prompt-", dir=root / "bench" / "runner") as directory:
        prompt_file = Path(directory) / "prompt.md"
        prompt_file.write_text(user_prompt, encoding="utf-8")
        started = time.monotonic()
        proc = subprocess.run([wrapper, "--model", model, "--thinking", thinking, "--prompt-file", str(prompt_file),
                               "--max-time", str(max_time)], cwd=root, capture_output=True, text=True, check=False)
        return proc, time.monotonic() - started


# Failures caused by the network or a provider, not the model. Only these are rerun on resume; a model failure
# (bad JSON, empty answer, run-cap deadline, omp loop guard) is a result and is never re-rolled at the same cap.
INFRA_FAILURE = re.compile(r"ECONNRESET|ETIMEDOUT|ENOTFOUND|socket connection was closed|fetch failed|"
                           r"Network connection lost|"
                           r"Provider returned error|\b(?:429|500|502|503|504)\b")


def _complete(path: Path, rerun_deadline: bool = False, max_time: int = MAX_TIME_S) -> bool:
    if not path.exists():
        return False
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, AttributeError) as exc:
        logger.warning("Ignoring corrupt run record %s: %s", path, exc)
        return False
    error = record.get("error") or ""
    # A deadline stop reruns only under a higher cap than it ran with, so a cap is never re-rolled.
    if rerun_deadline and DEADLINE.search(error) and record.get("max_time_s", LEGACY_MAX_TIME_S) < max_time:
        return False
    return record.get("exit_code") == 0 or not INFRA_FAILURE.search(error)


def execute(root: Path, key: str, rule: int, passage: str, repeat: int, framing: str, roster: dict, wrapper: str,
            force: bool = False, rerun_deadline: bool = False, max_time: int = MAX_TIME_S) -> dict | None:
    run_id = f"R{rule}_{passage}_r{repeat}" + ("_easy" if framing == "easy" else "")
    destination = root / "runs" / key / f"{run_id}.json"
    if not force and _complete(destination, rerun_deadline, max_time):
        logger.info("Skipping completed %s/%s", key, run_id)
        return None
    prompt = assemble(root, rule, passage, framing)
    model = roster["scored"][key]
    if model["thinking"] == "unverified":
        raise ValueError(f"Refusing {key}: thinking level is unverified")
    start = datetime.now(timezone.utc).isoformat()
    raw = []
    rate_limit_retries = 0
    proc, elapsed = _invoke(root, wrapper, model["model"], model["thinking"], prompt.user, max_time)
    duration = elapsed
    # Endpoint-busy errors are infrastructure, not model results: back off and resend, at most len(BUSY_WAITS)
    # times. 429 = OpenRouter provider rate limit; 503 = provider unavailable.
    # Every model gets exactly one model attempt; a bad answer is never retried.
    for wait in BUSY_WAITS:
        if not ENDPOINT_BUSY.search(proc.stdout):
            break
        logger.warning("Endpoint busy on %s/%s; waiting %ds", key, run_id, wait)
        raw.append(proc.stdout)
        rate_limit_retries += 1
        time.sleep(wait)
        proc, elapsed = _invoke(root, wrapper, model["model"], model["thinking"], prompt.user, max_time)
        duration += elapsed
    raw.append(proc.stdout)
    final = parse_events(proc.stdout)
    cost = final.cost_usd
    calls = list(final.tool_calls)
    totals = dict(final.usage)
    assert proc is not None and final is not None
    error = final.error or (f"omp exited {proc.returncode}: {proc.stderr.strip() or _last_error_message(proc.stdout)}"
                            if proc.returncode else None)
    if not final.output_text:
        error = error or "empty final assistant text"
    edits, parse_error, malformed = parse_edits(final.output_text)
    pin = _pin(root)
    record = {
        "run_id": run_id, "model_key": key, "endpoint_model": model["model"],
        "rule": rule, "passage": passage, "repeat": repeat,
        "framing": framing, "thinking": model["thinking"],
        "system_prompt_sha256": prompt.system_prompt_sha256, "prompt_sha256": prompt.prompt_sha256,
        "rule_text_sha256": prompt.rule_text_sha256, "passage_sha256": prompt.passage_sha256,
        "omp_version": pin.get("PROSEBENCH_OMP_VERSION"), "image_digest": pin.get("PROSEBENCH_IMAGE_DIGEST"),
        "started_at": start, "duration_s": duration, "max_time_s": max_time, "exit_code": proc.returncode,
        "error": error,
        "output_text": final.output_text, "edits": edits, "malformed_edits": malformed, "parse_error": parse_error,
        "usage": totals, "cost_usd": cost, "tool_calls": calls, "rate_limit_retries": rate_limit_retries,
    }
    _atomic_write(destination.with_suffix(".jsonl"), "".join(raw))
    _atomic_write(destination, json.dumps(record, ensure_ascii=True, indent=2) + "\n")
    return record


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", default="all", help="comma-separated scored model keys, or all")
    parser.add_argument("--rules", default="all", help="comma-separated rule numbers 1-5, or all")
    parser.add_argument("--passages", default="all", help="comma-separated P1-P3, or all")
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--framings", default="all", help="verbatim,easy, or all; easy applies only to rule 3")
    parser.add_argument("--pilot", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--rerun-deadline", action="store_true",
                        help="also rerun runs stopped by a lower run cap than --max-time")
    parser.add_argument("--max-time", type=int, default=MAX_TIME_S, help="run cap in seconds (omp --max-time)")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args(argv)
    try:
        roster = yaml.safe_load((ROOT / "bench" / "roster.yml").read_text(encoding="utf-8"))
        for name, entry in roster["scored"].items():
            if not isinstance(entry.get("thinking"), str):
                raise ValueError(f"roster scored.{name}.thinking must be a quoted string, got "
                                 f"{entry.get('thinking')!r} (YAML reads bare off/on as booleans)")
        keys = _selection(args.models, tuple(roster["scored"]), "models")
        rules = [int(item) for item in _selection(args.rules, tuple(str(n) for n in range(1, 6)), "rules")]
        passages = _selection(args.passages, ("P1", "P2", "P3"), "passages")
        framings = _selection(args.framings, ("verbatim", "easy"), "framings")
        repeats = args.repeats
        if repeats < 1:
            raise ValueError("--repeats must be positive")
        if args.pilot:
            passages, repeats, rules, framings = ["P1"], 1, list(range(1, 6)), ["verbatim", "easy"]
        plan = []
        for key in keys:
            for rule in rules:
                for passage in passages:
                    for repeat in range(1, repeats + 1):
                        for framing in framings:
                            if framing == "easy" and rule != 3:
                                continue
                            run_id = f"R{rule}_{passage}_r{repeat}" + ("_easy" if framing == "easy" else "")
                            plan.append((key, rule, passage, repeat, framing, run_id))
        print(f"Planned runs: {len(plan)}")
        if args.dry_run:
            for key, rule, passage, repeat, framing, run_id in plan:
                print(f"{key}/{run_id}")
            return 0
        if not args.yes:
            print("Refusing execution without --yes", file=sys.stderr)
            return 2
        for key in keys:
            if roster["scored"][key]["thinking"] == "unverified":
                raise ValueError(f"Refusing {key}: thinking level is unverified")
        wrapper = os.environ.get("PROSEBENCH_OMP_RUN", str(ROOT / "container" / "omp-run.sh"))
        failures = 0
        for key, rule, passage, repeat, framing, run_id in plan:
            record = execute(ROOT, key, rule, passage, repeat, framing, roster, wrapper, args.force,
                             args.rerun_deadline, args.max_time)
            if record is not None and (record["exit_code"] != 0 or record["error"] or record["parse_error"]):
                logger.warning("Failed %s/%s: %s", key, run_id, record["error"] or record["parse_error"])
                failures += 1
        return 1 if failures else 0
    except (ValueError, KeyError, OSError, yaml.YAMLError) as exc:
        logger.exception("Matrix run stopped: %s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
