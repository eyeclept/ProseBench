"""Audit the answer key with off-roster GPT-6.1 Sol and maintain the owner decision sheet.

Each audit call covers one passage (all rows, or only `--ids`) and is saved as
out/P{n}/audit.json (full) or out/P{n}/audit_<UTC stamp>.json (targeted), with
the compact rows it audited. The worksheet is rebuilt from every saved audit:
verdicts match the CURRENT key by (passage, rule, target_text), so rows that a
re-plant removed drop out and a later audit of the same row wins.

Outputs: out/audit_disagreements.md (readable) and out/audit_decisions.csv
(owner fills `decision` with keep, accept, or drop; existing decisions are
preserved across rebuilds). build_key applies the decisions.
Spend is projected before each call and capped at BUDGET per invocation.
"""

import argparse
import csv
import json
import logging
from datetime import datetime, timezone

from bench.corpus.common import ACTIONS, OUT, SOURCE, injected_text, parse_json, rules_text
from bench.llm_clients import openrouter_chat

logger = logging.getLogger(__name__)
MODEL = "openai/gpt-6.1-sol"
INPUT_RATE = 2.0 / 1_000_000
OUTPUT_RATE = 10.0 / 1_000_000
BUDGET = 0.50
MAX_TOKENS = 12000
KEY_FIELDS = ("instance_id", "rule", "kind", "subtype", "polarity", "expected_action", "target_text", "fact_text")
DECISIONS = OUT / "audit_decisions.csv"
DECISION_FIELDS = ("passage", "rule", "label", "target_text", "key_subtype", "key_polarity", "key_action",
                   "auditor_subtype", "auditor_polarity", "auditor_action", "auditor_reason", "suggested",
                   "decision", "owner_note")
R4_CLASS_FIXES = {"emdash_fragment", "emdash_clauses", "emdash_runon", "curly_quote", "endash_range"}

_NULLABLE = {"type": ["string", "null"]}
FORMAT = {"type": "json_schema", "json_schema": {"name": "audit", "strict": True, "schema": {
    "type": "object", "additionalProperties": False, "required": ["verdicts", "missed"],
    "properties": {
        "verdicts": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["instance_id", "verdict", "reason", "correct_subtype", "correct_polarity",
                         "correct_expected_action"],
            "properties": {"instance_id": {"type": "string"},
                           "verdict": {"type": "string", "enum": ["confirm", "dispute"]},
                           "reason": {"type": "string"}, "correct_subtype": _NULLABLE,
                           "correct_polarity": _NULLABLE, "correct_expected_action": _NULLABLE}}},
        "missed": {"type": "array", "items": {
            "type": "object", "additionalProperties": False,
            "required": ["rule", "subtype", "polarity", "expected_action", "target_text", "reason"],
            "properties": {"rule": {"type": "integer"}, "subtype": {"type": "string"},
                           "polarity": {"type": "string", "enum": ["change", "keep", "flag"]},
                           "expected_action": {"type": "string", "enum": sorted(ACTIONS)},
                           "target_text": {"type": "string"}, "reason": {"type": "string"}}}},
    }}}}


def _prompt(text: str, rows: list[dict], targeted: bool) -> str:
    missed = ("List no missed items; this is a targeted check of the rows given. " if targeted else
              "Then list every violation of rules 1-5 the key misses (native or planted), including non-ASCII "
              "characters for rule 4. Each missed target_text must be copied verbatim from the essay and occur "
              "there exactly once. ")
    return (
        "You are auditing an answer key for a prose-editing benchmark. Check EVERY key row against the essay and "
        "the frozen rules. Return one verdict per row: confirm, or dispute with the corrected subtype, polarity, "
        "or expected_action (null for any field you do not dispute). Dispute a replace_with_fact row whose "
        "fact_text does not directly measure the quantity the flagged word inflates, and any row that is not a "
        "real instance. " + missed + "Do not revise the essay or the key.\n\nFrozen rules:\n" + rules_text()
        + "\n\nAnswer key rows:\n" + json.dumps(rows, ensure_ascii=False) + "\n\nComplete essay:\n" + text
    )


def _load_key() -> list[dict]:
    return [json.loads(line) for line in (OUT / "answer_key.jsonl").read_text(encoding="utf-8").splitlines()]


def run_audit(ids: set[str] | None) -> float:
    rows = _load_key()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    spend = 0.0
    for passage in SOURCE:
        subset = [row for row in rows if row["passage"] == passage and (ids is None or row["instance_id"] in ids)]
        if not subset:
            continue
        text = injected_text(passage)
        compact = [{k: row[k] for k in KEY_FIELDS} for row in subset]
        prompt = _prompt(text, compact, targeted=ids is not None)
        projected = spend + len(prompt) / 3 * INPUT_RATE + MAX_TOKENS * OUTPUT_RATE
        if projected > BUDGET:
            raise ValueError(f"Audit projected spend ${projected:.4f} exceeds ${BUDGET:.2f} cap before {passage}")
        name = "audit.json" if ids is None else f"audit_{stamp}.json"
        reply = openrouter_chat(MODEL, [{"role": "user", "content": prompt}], max_tokens=MAX_TOKENS,
                                response_format=FORMAT, reasoning_effort="low",
                                log_path=OUT / passage / name.replace(".json", "_raw.json"))
        usage = reply["usage"]
        cost = usage.get("cost")
        if cost is None:
            cost = (usage.get("prompt_tokens") or 0) * INPUT_RATE + (usage.get("completion_tokens") or 0) * OUTPUT_RATE
        spend += float(cost)
        result = parse_json(reply["content"])
        result.update(model=reply["model"], usage=usage, cost_usd=cost, audited_rows=compact, created=stamp)
        (OUT / passage / name).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"{passage}: {len(result['verdicts'])}/{len(subset)} verdicts; {len(result['missed'])} missed; "
              f"${float(cost):.4f} -> {name}", flush=True)
        if spend > BUDGET:
            raise ValueError(f"Audit spend ${spend:.4f} exceeded ${BUDGET:.2f} cap after {passage}; stopped")
    print(f"OpenRouter spend this run: ${spend:.4f}", flush=True)
    return spend


def _audit_files(passage: str) -> list[dict]:
    files = sorted((OUT / passage).glob("audit*.json"))
    loaded = [json.loads(f.read_text(encoding="utf-8")) for f in files if not f.name.endswith("_raw.json")]
    return sorted(loaded, key=lambda a: a.get("created", ""))


def _suggest(rule: int, label: str, auditor_subtype: str | None) -> str:
    if label == "DISPUTE" and rule == 4 and auditor_subtype and (
            auditor_subtype in R4_CLASS_FIXES or auditor_subtype.startswith("endash")):
        return "accept"
    return "review"


def build_items() -> list[dict]:
    """Current open disagreements, matched to the current key by (passage, rule, target_text)."""
    key = {(row["passage"], row["rule"], row["target_text"]): row for row in _load_key()}
    items: dict[tuple, dict] = {}
    for passage in SOURCE:
        text = injected_text(passage)
        for audit in _audit_files(passage):
            audited = {row["instance_id"]: row for row in audit.get("audited_rows", [])}
            for verdict in audit["verdicts"]:
                old = audited.get(verdict["instance_id"])
                if old is None:
                    logger.warning("%s: verdict for unknown instance %s", passage, verdict["instance_id"])
                    continue
                stable = (passage, old["rule"], old["target_text"])
                current = key.get(stable)
                if current is None:
                    items.pop(stable + ("DISPUTE",), None)
                    continue
                if verdict["verdict"] == "confirm":
                    items.pop(stable + ("DISPUTE",), None)
                    continue
                items[stable + ("DISPUTE",)] = {
                    "passage": passage, "rule": old["rule"], "label": "DISPUTE", "target_text": old["target_text"],
                    "key_subtype": current["subtype"], "key_polarity": current["polarity"],
                    "key_action": current["expected_action"], "auditor_subtype": verdict["correct_subtype"] or "",
                    "auditor_polarity": verdict["correct_polarity"] or "",
                    "auditor_action": verdict["correct_expected_action"] or "", "auditor_reason": verdict["reason"],
                    "suggested": _suggest(old["rule"], "DISPUTE", verdict["correct_subtype"])}
            for miss in audit["missed"]:
                stable = (passage, miss["rule"], miss["target_text"])
                if stable in key:
                    continue
                count = text.count(miss["target_text"]) if miss["target_text"] else 0
                reason = miss["reason"] + ("" if count == 1 else f" [target occurs {count} times in essay]")
                items[stable + ("MISSED",)] = {
                    "passage": passage, "rule": miss["rule"], "label": "MISSED", "target_text": miss["target_text"],
                    "key_subtype": "", "key_polarity": "", "key_action": "", "auditor_subtype": miss["subtype"],
                    "auditor_polarity": miss["polarity"], "auditor_action": miss["expected_action"],
                    "auditor_reason": reason, "suggested": "review"}
    return list(items.values())


def write_worksheet() -> int:
    previous = {}
    if DECISIONS.exists():
        with DECISIONS.open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                previous[(row["passage"], int(row["rule"]), row["target_text"], row["label"])] = row
    items = build_items()
    for item in items:
        old = previous.get((item["passage"], item["rule"], item["target_text"], item["label"]), {})
        item["decision"] = old.get("decision", "")
        item["owner_note"] = old.get("owner_note", "")
    items.sort(key=lambda i: (i["passage"], i["rule"], i["label"], i["target_text"]))
    with DECISIONS.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=DECISION_FIELDS)
        writer.writeheader()
        writer.writerows(items)
    lines = ["# Answer-key audit disagreements", "",
             f"Auditor: {MODEL}. Fill the `decision` column of `audit_decisions.csv` with keep, accept, or drop.",
             "`accept` applies the auditor's correction (or adds a MISSED row); `drop` removes the key row; "
             "`keep` or blank leaves the key unchanged. `suggested` is the orchestrator's triage, not a decision.",
             ""]
    for item in items:
        lines += [f"## {item['passage']} R{item['rule']} {item['label']} (suggested: {item['suggested']})", "",
                  f"Target: `{item['target_text']}`", "",
                  f"Key: {item['key_subtype']} / {item['key_polarity']} / {item['key_action']}", "",
                  f"Auditor: {item['auditor_subtype']} / {item['auditor_polarity']} / {item['auditor_action']}", "",
                  f"Reason: {item['auditor_reason']}", ""]
    if not items:
        lines.append("No open disagreements.")
    (OUT / "audit_disagreements.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    counts = {}
    for item in items:
        counts[(item["label"], item["suggested"])] = counts.get((item["label"], item["suggested"]), 0) + 1
    print(f"Worksheet: {len(items)} open items {sorted(counts.items())}", flush=True)
    return len(items)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ids", default="", help="comma-separated instance_ids for a targeted audit")
    parser.add_argument("--worksheet-only", action="store_true", help="rebuild the worksheet without API calls")
    args = parser.parse_args()
    if not args.worksheet_only:
        run_audit(set(args.ids.split(",")) if args.ids else None)
    write_worksheet()


if __name__ == "__main__":
    main()
