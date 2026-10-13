"""Extract a seeded stratified sample of raw before/after instance text."""

import argparse
import csv
import difflib
import json
import logging
import math
import random
from collections import defaultdict
from pathlib import Path

from bench.score.apply_edits import apply_edits
from bench.score.score_runs import load_key, load_passage

logger = logging.getLogger(__name__)
FIELDS = ("run_id", "model_key", "rule", "passage", "repeat", "framing", "instance_id",
          "polarity", "kind", "subtype", "before", "after", "diff", "owner_label", "owner_notes")


def sample_records(records: list[tuple[dict, dict]], seed: int = 645) -> list[tuple[dict, dict]]:
    """Allocate 20 percent using largest remainders across fixed strata."""
    rng = random.Random(seed)
    strata = defaultdict(list)
    for run, item in records:
        strata[(run["rule"], run["model_key"], item["polarity"], item["kind"])].append((run, item))
    target = math.ceil(len(records) * 0.2)
    quota = {key: len(value) * 0.2 for key, value in strata.items()}
    count = {key: math.floor(value) for key, value in quota.items()}
    keys = sorted(strata)
    rng.shuffle(keys)
    keys.sort(key=lambda key: quota[key] - count[key], reverse=True)
    for key in keys[:target - sum(count.values())]:
        count[key] += 1
    chosen = []
    for key in sorted(strata):
        chosen.extend(rng.sample(strata[key], count[key]))
    return sorted(chosen, key=lambda pair: (pair[0]["run_id"], pair[1]["instance_id"]))


def extract(run: dict, row: dict, original: str) -> tuple[str, str]:
    """Show the original sentence and its provenance-traced revised counterpart."""
    before = row["context_sentence"]
    start = original.find(before)
    if start < 0 or not start <= row["char_start"] < row["char_end"] <= start + len(before):
        raise ValueError(f"Context sentence not found around {row['instance_id']}")
    applied = apply_edits(original, run.get("edits") or [])
    return before, applied.region(start, start + len(before))


def write_report(runs_dir: Path, answer_key: Path, corpus_dir: Path,
                 markdown_path: Path, csv_path: Path, seed: int = 645, all_records: bool = False) -> list[dict]:
    """Write a worksheet and CSV twin without judging the edits (a 20% sample, or every record with all_records)."""
    key = load_key(answer_key)
    records = []
    for path in sorted(runs_dir.glob("*/*.json")):
        run = json.loads(path.read_text(encoding="utf-8"))
        for item in key[run["passage"]]:
            if item["rule"] == run["rule"]:
                records.append((run, item))
    sample = (sorted(records, key=lambda pair: (pair[0]["model_key"], pair[0]["run_id"], pair[1]["instance_id"]))
              if all_records else sample_records(records, seed))
    passages = {}
    output = []
    for run, item in sample:
        passage = passages.setdefault(run["passage"], load_passage(corpus_dir, run["passage"]))
        before, after = extract(run, item, passage)
        output.append({"run_id": run["run_id"], "model_key": run["model_key"],
                       "rule": run["rule"], "passage": run["passage"],
                       "repeat": run["repeat"], "framing": run["framing"],
                       "instance_id": item["instance_id"], "polarity": item["polarity"],
                       "kind": item["kind"], "subtype": item["subtype"],
                       "before": before, "after": after,
                       "diff": "".join(difflib.unified_diff(
                           (before + "\n").splitlines(keepends=True),
                           (after + "\n").splitlines(keepends=True),
                           fromfile="before", tofile="after")),
                       "owner_label": "", "owner_notes": ""})
    for path in (markdown_path, csv_path):
        path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(output)
    with markdown_path.open("w", encoding="utf-8") as stream:
        stream.write("# Hand-scoring worksheet\n\n")
        scope = ("All records (full matrix)." if all_records else
                 "Sample: 20 percent, stratified by rule, model, polarity, and kind. Seed: " + str(seed) + ".")
        stream.write(scope + "\n\n")
        stream.write("| " + " | ".join(FIELDS) + " |\n")
        stream.write("| " + " | ".join("---" for _ in FIELDS) + " |\n")
        for row in output:
            cells = [str(row[field]).replace("|", "\\|").replace("\n", "<br>") for field in FIELDS]
            stream.write("| " + " | ".join(cells) + " |\n")
    return output


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs-dir", type=Path, default=Path("runs"))
    parser.add_argument("--answer-key", type=Path, default=Path("bench/corpus/out/answer_key.jsonl"))
    parser.add_argument("--corpus-dir", type=Path, default=Path("bench/corpus/out"))
    parser.add_argument("--markdown", type=Path, default=Path("scores/hand_review.md"))
    parser.add_argument("--csv", type=Path, default=Path("scores/hand_review.csv"))
    parser.add_argument("--seed", type=int, default=645)
    parser.add_argument("--all", action="store_true", help="write every record instead of the 20% sample")
    args = parser.parse_args()
    sample = write_report(args.runs_dir, args.answer_key, args.corpus_dir,
                          args.markdown, args.csv, args.seed, args.all)
    print(f"Wrote {len(sample)} instances")


if __name__ == "__main__":
    main()
