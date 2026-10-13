"""Plan and execute guarded ProseBench runs through the pinned omp wrapper."""

from __future__ import annotations

import argparse
import json
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
ZERO_USAGE = {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0, "reasoning": 0}


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


def _invoke(root: Path, wrapper: str, model: str, thinking: str, user_prompt: str) -> tuple[subprocess.CompletedProcess[str], float]:
    with tempfile.TemporaryDirectory(prefix=".prompt-", dir=root / "bench" / "runner") as directory:
        prompt_file = Path(directory) / "prompt.md"
        prompt_file.write_text(user_prompt, encoding="utf-8")
        started = time.monotonic()
        proc = subprocess.run([wrapper, "--model", model, "--thinking", thinking, "--prompt-file", str(prompt_file)], cwd=root, capture_output=True, text=True, check=False)
        return proc, time.monotonic() - started


def _complete(path: Path) -> bool:
    if not path.exists():
        return False
    try:
        return json.loads(path.read_text(encoding="utf-8")).get("exit_code") == 0
    except (json.JSONDecodeError, AttributeError) as exc:
        logger.warning("Ignoring corrupt run record %s: %s", path, exc)
        return False


def execute(root: Path, key: str, rule: int, passage: str, repeat: int, framing: str, roster: dict, wrapper: str, force: bool = False, column_fallback: bool = False) -> dict | None:
    run_id = f"R{rule}_{passage}_r{repeat}" + ("_easy" if framing == "easy" else "")
    destination = root / "runs" / key / f"{run_id}.json"
    if not force and _complete(destination):
        logger.info("Skipping completed %s/%s", key, run_id)
        return None
    prompt = assemble(root, rule, passage, framing)
    models = roster["scored"]
    route = roster.get("routing", {})
    fallback_key = "qwen36"
    model = models[key]
    projection = (len(prompt.system) + len(prompt.user)) / 3.5 + route.get("harness_overhead_tokens", 0) + 4000
    if "harness_overhead_tokens" not in route:
        logger.warning("routing.harness_overhead_tokens missing; using zero")
    routed = key == "ornith" and (column_fallback or projection > route["t1_projection_limit_tokens"])
    route_reason = ("t1_column_fallback" if column_fallback else "projected_over_60000") if routed else None
    if routed:
        model = roster["fallback"][fallback_key]
    if model["thinking"] == "unverified":
        raise ValueError(f"Refusing {key}: thinking level for {fallback_key if routed else key} is unverified")
    start = datetime.now(timezone.utc).isoformat()
    raw = []
    totals = ZERO_USAGE.copy()
    calls = []
    cost = 0.0
    duration = 0.0
    attempts = 1 if key != "ornith" or routed else 3
    final = None
    proc = None
    for attempt in range(attempts):
        if attempt == 2:
            model = roster["fallback"][fallback_key]
            if model["thinking"] == "unverified":
                raise ValueError("Refusing ornith fallback: thinking level for qwen36 is unverified")
            routed = True
            route_reason = "t1_failure"
        proc, elapsed = _invoke(root, wrapper, model["model"], model["thinking"], prompt.user)
        duration += elapsed
        raw.append(proc.stdout)
        final = parse_events(proc.stdout)
        cost += final.cost_usd
        calls.extend(final.tool_calls)
        for name in totals:
            totals[name] += final.usage[name]
        if proc.returncode == 0 and not final.error and final.output_text:
            break
        if key != "ornith" or routed:
            break
        logger.warning("Ornith attempt %d failed for %s: %s", attempt + 1, run_id, final.error or proc.stderr.strip() or f"exit {proc.returncode} / empty response")
    assert proc is not None and final is not None
    error = final.error or (f"omp exited {proc.returncode}: {proc.stderr.strip()}" if proc.returncode else None)
    if not final.output_text:
        error = error or "empty final assistant text"
    edits, parse_error = parse_edits(final.output_text)
    pin = _pin(root)
    record = {
        "run_id": run_id, "model_key": key, "endpoint_model": model["model"], "routed": routed,
        "route_reason": route_reason, "rule": rule, "passage": passage, "repeat": repeat,
        "framing": framing, "thinking": model["thinking"],
        "system_prompt_sha256": prompt.system_prompt_sha256, "prompt_sha256": prompt.prompt_sha256,
        "rule_text_sha256": prompt.rule_text_sha256, "passage_sha256": prompt.passage_sha256,
        "omp_version": pin.get("PROSEBENCH_OMP_VERSION"), "image_digest": pin.get("PROSEBENCH_IMAGE_DIGEST"),
        "started_at": start, "duration_s": duration, "exit_code": proc.returncode, "error": error,
        "output_text": final.output_text, "edits": edits, "parse_error": parse_error,
        "usage": totals, "cost_usd": cost, "tool_calls": calls,
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
    parser.add_argument("--t1-column-fallback", action="store_true")
    parser.add_argument("--yes", action="store_true")
    args = parser.parse_args(argv)
    try:
        roster = yaml.safe_load((ROOT / "bench" / "roster.yml").read_text(encoding="utf-8"))
        for section in ("scored", "fallback"):
            for name, entry in roster[section].items():
                if not isinstance(entry.get("thinking"), str):
                    raise ValueError(f"roster {section}.{name}.thinking must be a quoted string, got "
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
        route = roster.get("routing", {})
        overhead = route.get("harness_overhead_tokens", 0)
        if "harness_overhead_tokens" not in route:
            logger.warning("routing.harness_overhead_tokens missing; using zero")
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
                prompt = assemble(ROOT, rule, passage, framing)
                projected = (len(prompt.system) + len(prompt.user)) / 3.5 + overhead + 4000
                print(f"{key}/{run_id} projected_tokens={projected:.1f}")
            return 0
        if not args.yes:
            print("Refusing execution without --yes", file=sys.stderr)
            return 2
        for key in keys:
            if roster["scored"][key]["thinking"] == "unverified" and not (key == "ornith" and args.t1_column_fallback):
                raise ValueError(f"Refusing {key}: thinking level is unverified")
        wrapper = os.environ.get("PROSEBENCH_OMP_RUN", str(ROOT / "container" / "omp-run.sh"))
        failures = 0
        for key, rule, passage, repeat, framing, run_id in plan:
            record = execute(ROOT, key, rule, passage, repeat, framing, roster, wrapper, args.force, args.t1_column_fallback)
            if record is not None and (record["exit_code"] != 0 or record["error"] or record["parse_error"]):
                logger.warning("Failed %s/%s: %s", key, run_id, record["error"] or record["parse_error"])
                failures += 1
        return 1 if failures else 0
    except (ValueError, KeyError, OSError, yaml.YAMLError) as exc:
        logger.exception("Matrix run stopped: %s", exc)
        return 2


if __name__ == "__main__":
    sys.exit(main())
