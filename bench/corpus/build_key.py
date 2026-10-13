"""Merge inventoried and planted instances, apply owner audit decisions, and validate the scored answer key.

Owner decisions come from out/audit_decisions.csv (written by bench.corpus.audit). They match rows by
(passage, rule, target_text), so they survive rebuilds and re-plants:
- DISPUTE accept: apply the auditor's subtype/polarity/action. An auditor subtype outside the vocabulary becomes
  `other` with the auditor's label in notes; polarity/action stay unless the auditor gave valid ones.
- DISPUTE drop: remove the row.
- MISSED accept: add a native row (target must occur once in the injected passage).
- keep or blank: no change.
"""

import argparse
import collections
import csv
import json
import logging

from bench.corpus.common import (ACTIONS, OUT, REQUIRED, SOURCE, check_quota, context_sentence, injected_text,
                                 normalize, source_text, validate_instance)
from bench.corpus.inject import apply_ops
from bench.corpus.coverage import uncovered

logger = logging.getLogger(__name__)
DECISIONS = OUT / "audit_decisions.csv"


def _corrected(row: dict, subtype: str, polarity: str, action: str) -> dict:
    rule = row["rule"]
    if subtype and subtype in REQUIRED[rule]:
        row["subtype"] = subtype
        return normalize(row)
    if subtype:
        row["subtype"] = "other"
        row["notes"] = (row.get("notes") or "") + f" [auditor subtype: {subtype}]"
    if polarity in ("change", "keep", "flag"):
        row["polarity"] = polarity
    if action in ACTIONS:
        row["expected_action"] = action
    return row


def apply_decisions(rows: list[dict]) -> list[dict]:
    if not DECISIONS.exists():
        return rows
    with DECISIONS.open(encoding="utf-8", newline="") as stream:
        decisions = [d for d in csv.DictReader(stream) if d["decision"].strip().lower() in ("accept", "drop")]
    index = {(r["passage"], r["rule"], r["target_text"]): r for r in rows}
    dropped = set()
    for d in decisions:
        stable = (d["passage"], int(d["rule"]), d["target_text"])
        choice = d["decision"].strip().lower()
        if d["label"] == "DISPUTE":
            row = index.get(stable)
            if row is None:
                logger.warning("Decision for a row no longer in the key: %s", stable)
                continue
            if choice == "drop":
                dropped.add(stable)
            else:
                _corrected(row, d["auditor_subtype"], d["auditor_polarity"], d["auditor_action"])
        elif choice == "accept" and stable not in index:
            text = injected_text(d["passage"])
            if text.count(d["target_text"]) != 1:
                logger.warning("Skipping MISSED accept; target not unique in %s: %r", d["passage"],
                               d["target_text"][:80])
                continue
            row = {"passage": d["passage"], "rule": int(d["rule"]), "kind": "native", "subtype": "other",
                   "polarity": "change", "expected_action": "cut", "target_text": d["target_text"],
                   "fact_text": None, "notes": "added from audit: " + d["auditor_reason"]}
            rows.append(_corrected(row, d["auditor_subtype"], d["auditor_polarity"], d["auditor_action"]))
            index[stable] = row
    kept = [r for r in rows if (r["passage"], r["rule"], r["target_text"]) not in dropped]
    print(f"Applied {len(decisions)} owner decisions ({len(dropped)} drops)")
    return kept


def build() -> list[dict]:
    items = []
    for passage in SOURCE:
        directory = OUT / passage
        text = injected_text(passage)
        original = source_text(passage)
        ops = json.loads((directory / "operations.json").read_text(encoding="utf-8"))
        if apply_ops(original, ops) != text:
            raise ValueError(f"Injected essay differs from declared operations: {passage}")
        native = json.loads((directory / "inventory.json").read_text(encoding="utf-8"))
        planted = json.loads((directory / "planted.json").read_text(encoding="utf-8"))
        for item in native + planted:
            row = dict(item)
            if row.get("passage") != passage:
                raise ValueError(f"Wrong passage in {passage} inventory")
            row.setdefault("fact_text", None)
            row.setdefault("notes", "")
            items.append(row)
    items = apply_decisions(items)
    rows = []
    serial = collections.Counter()
    for row in items:
        text = injected_text(row["passage"])
        serial[(row["passage"], row["rule"])] += 1
        row["instance_id"] = f"{row['passage']}-R{row['rule']}-{serial[(row['passage'], row['rule'])]:03d}"
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
