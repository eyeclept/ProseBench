"""Score every run against answer-key instances and write two CSV files."""

import argparse
import csv
import json
import logging
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from bench.score.apply_edits import apply_edits
from bench.score.deterministic import assess, collateral, fabricated_numbers, numbers, outcome
from bench.score.judge import judge_run
from bench.score.rule4 import keyboard_violations

logger = logging.getLogger(__name__)

INSTANCE_FIELDS = ("run_id", "model_key", "endpoint_model", "rule", "passage", "repeat",
                   "framing", "instance_id", "kind", "polarity", "subtype", "expected_action",
                   "outcome", "label", "flags", "judge_reason", "ordinary_cut",
                   "field_specific_promoted", "ambiguous_flagged")
RUN_FIELDS = ("run_id", "model_key", "endpoint_model", "rule", "passage", "repeat", "framing",
              "thinking", "cost_usd", "usage_input", "usage_output",
              "usage_cache_read", "usage_cache_write", "usage_reasoning", "duration_s", "max_time_s",
              "parse_error", "invalid_edit_count", "malformed_edit_count", "n_tool_calls", "firecrawl_called",
              "TP", "FN", "FP", "TN", "precision", "recall", "collateral_count",
              "other_rule_instance", "uncatalogued_text", "nonkeyboard_remaining",
              "fabricated_numbers", "ordinary_cut", "field_specific_promoted", "ambiguous_flagged")
RULE3_BINARIES = {"ordinary": "ordinary_cut", "field_specific": "field_specific_promoted",
                  "ambiguous": "ambiguous_flagged"}


def load_key(path: Path) -> dict[str, list[dict]]:
    """Load the fixed catalogue, grouped by passage ID."""
    grouped = {}
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            if line.strip():
                row = json.loads(line)
                grouped.setdefault(row["passage"], []).append(row)
    return grouped


def load_passage(corpus_dir: Path, passage: str) -> str:
    return (corpus_dir / passage / "injected.md").read_text(encoding="utf-8")


def score_one(run: dict, all_rows: list[dict], passage: str,
              cache_dir: Path) -> tuple[list[dict], dict]:
    """Score one run; parse failures count as no actions, never as retries."""
    selected = [row for row in all_rows if row["rule"] == run["rule"]]
    if not selected:
        raise ValueError(f"No answer-key instances for {run['run_id']}")
    for row in all_rows:
        start, end = row["char_start"], row["char_end"]
        if passage[start:end] != row["target_text"]:
            raise ValueError(f"Answer-key span mismatch: {row['instance_id']}")
    failed = bool(run.get("parse_error") or run.get("edits") is None)
    edits = [] if failed else run["edits"]
    applied = apply_edits(passage, edits)
    nonkeyboard = keyboard_violations(
        applied.text, applied.provenance,
        [row for row in all_rows if row["rule"] == 4 and row["subtype"] == "diacritic"], passage)
    extra = collateral(applied.edit_spans, selected, all_rows)
    results = []
    review = []
    for row in selected:
        state = outcome(row, applied.edit_spans)
        revised = applied.region(row["char_start"], row["char_end"])
        verdict, flags = assess(row, state, passage, revised, applied)
        if failed:
            flags.append("parse_error")
        touching = [span for span in applied.edit_spans if span.overlaps(row["char_start"], row["char_end"])
                    and span.status in ("applied", "ambiguous_applied")]
        fabricated = sorted({number for span in touching for number in numbers(span.replacement or "")
                             if number not in numbers(passage)})
        if fabricated:
            flags.append("fabricated_number")
            verdict = "incorrect"
        if verdict is None:
            review.append({"instance_id": row["instance_id"], "rule": row["rule"],
                           "subtype": row["subtype"], "polarity": row["polarity"],
                           "expected_action": row["expected_action"],
                           "target_text": row["target_text"], "fact_text": row.get("fact_text"),
                           "context_sentence": row["context_sentence"], "after_region": revised})
        results.append((row, state, flags, verdict))
    # Run stems repeat across model folders; include the folder key in the cache identity.
    judged = judge_run(f"{run['model_key']}/{run['run_id']}", passage, applied.text,
                       review, cache_dir) if review else {}
    instance_rows = []
    counts = Counter()
    binary = Counter()
    binary_totals = Counter()
    for row, state, flags, verdict in results:
        answer = judged.get(row["instance_id"])
        if answer:
            verdict = answer["verdict"]
        if verdict not in ("correct", "incorrect"):
            raise ValueError(f"Missing verdict: {row['instance_id']}")
        label = ("TP" if verdict == "correct" else "FN") if row["polarity"] != "keep" else (
            "TN" if verdict == "correct" else "FP")
        counts[label] += 1
        base = {key: run.get(key, "") for key in INSTANCE_FIELDS[:7]}
        base.update({key: row[key] for key in ("instance_id", "kind", "polarity", "subtype", "expected_action")})
        base.update(outcome=state, label=label, flags=json.dumps(flags),
                    judge_reason=answer["reason"] if answer else "")
        for key in RULE3_BINARIES.values():
            base[key] = ""
        if row["rule"] == 3 and row["subtype"] in RULE3_BINARIES:
            key = RULE3_BINARIES[row["subtype"]]
            base[key] = int(label == "TP")
            binary[key] += base[key]
            binary_totals[key] += 1
        instance_rows.append(base)
    tool_calls = run.get("tool_calls") or []
    usage = run.get("usage") or {}
    run_row = {key: run.get(key, "") for key in RUN_FIELDS[:7]}
    for key in ("thinking", "cost_usd", "duration_s"):
        run_row[key] = run.get(key, "")
    # Run records written before max_time_s existed ran under the original 600 s cap.
    run_row["max_time_s"] = run.get("max_time_s", 600)
    for key in ("input", "output", "cache_read", "cache_write", "reasoning"):
        run_row[f"usage_{key}"] = usage.get(key, 0)
    run_row.update(parse_error=failed, invalid_edit_count=sum(span.status == "invalid" for span in applied.edit_spans),
                   malformed_edit_count=len(run.get("malformed_edits") or []),
                   n_tool_calls=len(tool_calls), firecrawl_called=any("firecrawl" in str(call.get("name", "")).lower()
                                                                for call in tool_calls))
    for key in ("TP", "FN", "FP", "TN"):
        run_row[key] = counts[key]
    tp, fp, fn = counts["TP"], counts["FP"], counts["FN"]
    run_row.update(precision=tp / (tp + fp) if tp + fp else "",
                   recall=tp / (tp + fn) if tp + fn else "",
                   collateral_count=len(extra), other_rule_instance=sum(item["category"] == "other_rule_instance" for item in extra),
                   uncatalogued_text=sum(item["category"] == "uncatalogued_text" for item in extra),
                   nonkeyboard_remaining=json.dumps(nonkeyboard, ensure_ascii=True),
                   fabricated_numbers=json.dumps(fabricated_numbers(passage, applied)))
    for key in RULE3_BINARIES.values():
        run_row[key] = int(binary_totals[key] > 0 and binary[key] == binary_totals[key]) if run["rule"] == 3 else ""
    return instance_rows, run_row


def _score_path(path: Path, key: dict, corpus_dir: Path, scores_dir: Path) -> tuple[list[dict], dict]:
    run = json.loads(path.read_text(encoding="utf-8"))
    if run["run_id"] != path.stem:
        raise ValueError(f"Run ID does not match filename: {path}")
    passage_id = run["passage"]
    return score_one(run, key[passage_id], load_passage(corpus_dir, passage_id), scores_dir / "judge_cache")


def score_runs(runs_dir: Path, answer_key: Path, corpus_dir: Path,
               scores_dir: Path, workers: int = 8) -> tuple[list[dict], list[dict]]:
    """Score all JSON run records and create the instance/run CSV files.

    Runs score in parallel threads: the Grok judge call per run is network-bound, and each run's
    judge-cache files are keyed by its own model-qualified run_id, so threads never share a file.
    """
    key = load_key(answer_key)
    instances = []
    run_rows = []
    paths = sorted(runs_dir.glob("*/*.json"))
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for rows, summary in pool.map(lambda path: _score_path(path, key, corpus_dir, scores_dir), paths):
            instances.extend(rows)
            run_rows.append(summary)
    scores_dir.mkdir(parents=True, exist_ok=True)
    for name, rows, fields in (("instances.csv", instances, INSTANCE_FIELDS),
                               ("runs.csv", run_rows, RUN_FIELDS)):
        with (scores_dir / name).open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    return instances, run_rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-dir", type=Path, default=Path("runs"))
    parser.add_argument("--answer-key", type=Path, default=Path("bench/corpus/out/answer_key.jsonl"))
    parser.add_argument("--corpus-dir", type=Path, default=Path("bench/corpus/out"))
    parser.add_argument("--scores-dir", type=Path, default=Path("scores"))
    parser.add_argument("--workers", type=int, default=8, help="parallel runs (Grok judge calls)")
    args = parser.parse_args()
    instances, runs = score_runs(args.runs_dir, args.answer_key, args.corpus_dir, args.scores_dir, args.workers)
    print(f"Scored {len(instances)} instances in {len(runs)} runs")


if __name__ == "__main__":
    main()
