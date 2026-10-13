"""Merge inventoried and planted instances and validate the scored answer key."""

import argparse
import collections
import json
import logging

from bench.corpus.common import OUT, SOURCE, check_quota, context_sentence, injected_text, source_text, validate_instance
from bench.corpus.inject import apply_ops
from bench.corpus.coverage import uncovered

logger = logging.getLogger(__name__)


def build() -> list[dict]:
    rows = []
    for passage in SOURCE:
        directory = OUT / passage
        text = injected_text(passage)
        original = source_text(passage)
        ops = json.loads((directory / "operations.json").read_text(encoding="utf-8"))
        if apply_ops(original, ops) != text:
            raise ValueError(f"Injected essay differs from declared operations: {passage}")
        native = json.loads((directory / "inventory.json").read_text(encoding="utf-8"))
        planted = json.loads((directory / "planted.json").read_text(encoding="utf-8"))
        serial = collections.Counter()
        for item in native + planted:
            row = dict(item)
            if row.get("passage") != passage:
                raise ValueError(f"Wrong passage in {passage} inventory")
            row.setdefault("fact_text", None)
            row.setdefault("notes", "")
            serial[row["rule"]] += 1
            row["instance_id"] = f"{passage}-R{row['rule']}-{serial[row['rule']]:03d}"
            row["char_start"] = text.find(row["target_text"])
            row["char_end"] = row["char_start"] + len(row["target_text"])
            row["context_sentence"] = context_sentence(text, row["char_start"], row["char_end"])
            validate_instance(row, text, keyed=True)
            rows.append(row)
    for passage in SOURCE:
        missing = uncovered(source_text(passage), [
            row for row in rows if row["passage"] == passage and row["kind"] == "native"
            and row["target_text"] in source_text(passage)
        ])
        if missing:
            raise ValueError(f"Uncatalogued native Rule 4 characters: {passage} positions {missing[:30]} ({len(missing)} total)")
    check_quota(rows)
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "answer_key.jsonl").write_text("".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    return rows


def check() -> list[dict]:
    rows = [json.loads(line) for line in (OUT / "answer_key.jsonl").read_text(encoding="utf-8").splitlines()]
    seen = set()
    for row in rows:
        validate_instance(row, injected_text(row["passage"]), keyed=True)
        if row["instance_id"] in seen:
            raise ValueError(f"Duplicate instance ID: {row['instance_id']}")
        seen.add(row["instance_id"])
    for passage in SOURCE:
        missing = uncovered(source_text(passage), [
            row for row in rows if row["passage"] == passage and row["kind"] == "native"
            and row["target_text"] in source_text(passage)
        ])
        if missing:
            raise ValueError(f"Uncatalogued native Rule 4 characters: {passage} positions {missing[:30]} ({len(missing)} total)")
    check_quota(rows)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    rows = check() if args.check else build()
    print(f"Validated {len(rows)} answer-key rows across {len(SOURCE)} passages")
    counts = collections.Counter((row["passage"], row["rule"], row["kind"], row["polarity"]) for row in rows)
    for key, count in sorted(counts.items()):
        print(*key, count)


if __name__ == "__main__":
    main()
