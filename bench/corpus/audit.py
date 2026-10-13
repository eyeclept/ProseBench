"""Audit the completed corpus with off-roster GPT-6.1 Sol.

One call per passage with compact answer-key rows and a strict JSON schema.
Anomalies (missing verdicts, a 'missed' target that is absent or non-unique)
go into the owner worksheet as items to check; they never abort the audit.
Spend is projected before each call and capped at BUDGET.
"""

import argparse
import json
import logging

from bench.corpus.common import ACTIONS, OUT, SOURCE, injected_text, parse_json, rules_text
from bench.llm_clients import openrouter_chat

logger = logging.getLogger(__name__)
MODEL = "openai/gpt-6.1-sol"
INPUT_RATE = 2.0 / 1_000_000
OUTPUT_RATE = 10.0 / 1_000_000
BUDGET = 0.50
MAX_TOKENS = 12000
KEY_FIELDS = ("instance_id", "rule", "kind", "subtype", "polarity", "expected_action", "target_text", "fact_text")

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


def _prompt(text: str, rows: list[dict]) -> str:
    return (
        "You are auditing an answer key for a prose-editing benchmark. Check EVERY key row against the essay and "
        "the frozen rules. Return one verdict per row: confirm, or dispute with the corrected subtype, polarity, "
        "or expected_action (null for any field you do not dispute). Dispute a replace_with_fact row whose "
        "fact_text does not support a replacement, and any row that is not a real instance. Then list every "
        "violation of rules 1-5 the key misses (native or planted), including non-ASCII characters for rule 4. "
        "Each missed target_text must be copied verbatim from the essay and occur there exactly once. Do not "
        "revise the essay or the key.\n\nFrozen rules:\n" + rules_text()
        + "\n\nAnswer key rows:\n" + json.dumps(rows, ensure_ascii=False)
        + "\n\nComplete essay:\n" + text
    )


def _worksheet(items: list[tuple]) -> str:
    lines = ["# Answer-key audit disagreements", "",
             "Auditor: openai/gpt-6.1-sol. For each item, write keep-key, accept-auditor, or a custom fix.", ""]
    for passage, label, sentence, reason, detail in items:
        lines += [f"## {passage} {label}", "", f"Text: {sentence}", "", f"Auditor reason: {reason}", "",
                  f"Detail: `{json.dumps(detail, ensure_ascii=True)}`", "", "Decision: ____________________", ""]
    if not items:
        lines.append("No disputes or missed items reported.")
    return "\n".join(lines) + "\n"


def audit() -> tuple[int, float]:
    rows = [json.loads(line) for line in (OUT / "answer_key.jsonl").read_text(encoding="utf-8").splitlines()]
    spend = 0.0
    items = []
    for passage in SOURCE:
        text = injected_text(passage)
        subset = [row for row in rows if row["passage"] == passage]
        compact = [{k: row[k] for k in KEY_FIELDS} for row in subset]
        prompt = _prompt(text, compact)
        projected = spend + len(prompt) / 3 * INPUT_RATE + MAX_TOKENS * OUTPUT_RATE
        if projected > BUDGET:
            raise ValueError(f"Audit projected spend ${projected:.4f} exceeds ${BUDGET:.2f} cap before {passage}")
        reply = openrouter_chat(MODEL, [{"role": "user", "content": prompt}], max_tokens=MAX_TOKENS,
                                response_format=FORMAT, reasoning_effort="low",
                                log_path=OUT / passage / "audit_raw.json")
        usage = reply["usage"]
        cost = usage.get("cost")
        if cost is None:
            cost = (usage.get("prompt_tokens") or 0) * INPUT_RATE + (usage.get("completion_tokens") or 0) * OUTPUT_RATE
        spend += float(cost)
        result = parse_json(reply["content"])
        result.update(model=reply["model"], usage=usage, cost_usd=cost)
        (OUT / passage / "audit.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                                                  encoding="utf-8")
        by_id = {row["instance_id"]: row for row in subset}
        received = [v["instance_id"] for v in result["verdicts"]]
        for missing_id in sorted(set(by_id) - set(received)):
            logger.warning("%s: auditor returned no verdict for %s", passage, missing_id)
            items.append((passage, missing_id, by_id[missing_id]["context_sentence"],
                          "auditor returned no verdict for this row", by_id[missing_id]))
        for verdict in result["verdicts"]:
            row = by_id.get(verdict["instance_id"])
            if row is None:
                items.append((passage, verdict["instance_id"], "", "auditor cited an unknown instance_id", verdict))
            elif verdict["verdict"] == "dispute":
                items.append((passage, row["instance_id"], row["context_sentence"], verdict["reason"],
                              {"key": {k: row[k] for k in KEY_FIELDS}, "auditor": verdict}))
        for miss in result["missed"]:
            count = text.count(miss["target_text"]) if miss["target_text"] else 0
            note = "" if count == 1 else f" [target occurs {count} times in essay]"
            items.append((passage, "MISSED", miss["target_text"], miss["reason"] + note, miss))
        print(f"{passage}: {len(result['verdicts'])}/{len(subset)} verdicts; {len(result['missed'])} missed; "
              f"${float(cost):.4f}", flush=True)
        if spend > BUDGET:
            raise ValueError(f"Audit spend ${spend:.4f} exceeded ${BUDGET:.2f} cap after {passage}; stopped")
    (OUT / "audit_disagreements.md").write_text(_worksheet(items), encoding="utf-8")
    print(f"Worksheet items: {len(items)}; OpenRouter spend: ${spend:.4f}", flush=True)
    return len(items), spend


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    argparse.ArgumentParser(description=__doc__.splitlines()[0]).parse_args()
    audit()


if __name__ == "__main__":
    main()
