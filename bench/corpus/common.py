"""Shared passage, classification, and answer-key validation utilities."""

import json
import logging
from pathlib import Path
import re

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "out"
SOURCE = {"P1": "Cybersecurity.md", "P2": "PowerSystems.md", "P3": "Botany.md"}
REQUIRED = {
    1: {"fact_available": ("change", "replace_with_fact"), "no_fact": ("change", "cut"), "technical_term": ("keep", "keep")},
    2: {"windup": ("change", "cut"), "loadbearing": ("keep", "keep"), "doubling": ("change", "cut")},
    3: {"ordinary": ("change", "cut"), "field_specific": ("change", "promote_to_sentence"), "ambiguous": ("flag", "flag")},
    4: {"emdash_clauses": ("change", "punct_semicolon_or_period"), "emdash_fragment": ("change", "punct_comma"), "emdash_runon": ("change", "punct_split"), "endash_range": ("change", "punct_hyphen"), "curly_quote": ("change", "punct_straight_quote"), "ellipsis": ("change", "punct_three_periods"), "diacritic": ("keep", "keep"), "other_nonkeyboard": ("change", "ascii_equivalent")},
    5: {"number_available": ("change", "replace_with_fact"), "no_number": ("change", "cut"), "finality_exclusive": ("change", "cut"), "emphatic_no_exclusive": ("keep", "keep")},
}
ACTIONS = {action for rule in REQUIRED.values() for _, action in rule.values()}
ACTIONS.add("ascii_equivalent")
FIELDS = {"instance_id", "passage", "rule", "kind", "polarity", "subtype", "expected_action", "target_text", "char_start", "char_end", "context_sentence", "fact_text", "notes"}


def source_text(passage: str) -> str:
    return (ROOT / "Essays/gpt-oss-120b" / SOURCE[passage]).read_text(encoding="utf-8")


def injected_text(passage: str) -> str:
    return (OUT / passage / "injected.md").read_text(encoding="utf-8")


def rules_text() -> str:
    paths = [ROOT / "bench/rules" / f"rule{rule}.md" for rule in range(1, 6)]
    paths.append(ROOT / "bench/rules/banned-words-phrases.md")
    return "\n\n".join(f"# {path.name}\n{path.read_text(encoding='utf-8')}" for path in paths)


def parse_json(content: str) -> dict:
    text = content.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    start = text.find("{")
    if start < 0:
        raise ValueError("Model returned no JSON object")
    result, _ = json.JSONDecoder().raw_decode(text[start:])
    if not isinstance(result, dict):
        raise ValueError("Model returned a non-object JSON value")
    return result


def context_sentence(text: str, start: int, end: int) -> str:
    left = max(text.rfind("\n", 0, start), *(text.rfind(mark, 0, start) for mark in ".!?")) + 1
    right_candidates = [pos for mark in ".!?\n" if (pos := text.find(mark, end)) >= 0]
    right = min(right_candidates) + 1 if right_candidates else len(text)
    return text[left:right].strip()


def validate_instance(row: dict, text: str, *, keyed: bool = False) -> None:
    passage = row.get("passage")
    rule = row.get("rule")
    subtype = row.get("subtype")
    target = row.get("target_text")
    if passage not in SOURCE or type(rule) is not int or rule not in REQUIRED:
        raise ValueError(f"Invalid passage or rule: {passage}, {rule}")
    if subtype not in REQUIRED[rule] and subtype != "other":
        raise ValueError(f"Unknown subtype: {subtype}")
    if subtype == "other" and not row.get("notes"):
        raise ValueError("Other subtype requires a note")
    if row.get("kind") not in ("native", "planted"):
        raise ValueError("Invalid kind")
    if subtype in REQUIRED[rule] and (row.get("polarity"), row.get("expected_action")) != REQUIRED[rule][subtype]:
        raise ValueError(f"Wrong classification: {passage} R{rule} {subtype}")
    if row.get("polarity") not in ("change", "keep", "flag") or row.get("expected_action") not in ACTIONS:
        raise ValueError("Invalid polarity or action")
    if not isinstance(target, str) or not target or text.count(target) != 1:
        raise ValueError(f"Target missing or nonunique: {passage} R{rule} {repr(target)[:110]}")
    fact = row.get("fact_text")
    if fact is not None and (not isinstance(fact, str) or not fact or fact not in text):
        raise ValueError(f"Fact not present in passage: {passage} R{rule}")
    if row.get("expected_action") == "replace_with_fact" and not fact:
        raise ValueError(f"Replacement fact missing: {passage} R{rule}")
    if keyed:
        if set(row) != FIELDS:
            raise ValueError(f"Answer key fields differ: {set(row) ^ FIELDS}")
        start, end = row["char_start"], row["char_end"]
        if type(start) is not int or type(end) is not int or text[start:end] != target or text.find(target) != start or end != start + len(target):
            raise ValueError(f"Invalid target span: {row['instance_id']}")
        if row["context_sentence"] != context_sentence(text, start, end):
            raise ValueError(f"Invalid context sentence: {row['instance_id']}")
        if not isinstance(row["notes"], str) or not re.fullmatch(r"P[123]-R[1-5]-\d{3,}", row["instance_id"]):
            raise ValueError("Invalid notes or instance ID")


def check_quota(rows: list[dict]) -> None:
    for passage in SOURCE:
        for rule, subtypes in REQUIRED.items():
            present = {row["subtype"] for row in rows if row["passage"] == passage and row["rule"] == rule}
            missing = set(subtypes) - present
            if missing:
                raise ValueError(f"Subtype quota gap: {passage} R{rule}: {', '.join(sorted(missing))}")


def normalize(row: dict) -> dict:
    """Force polarity/expected_action from the subtype table; keep model values only for subtype 'other'."""
    mapping = REQUIRED[row["rule"]]
    if row.get("subtype") in mapping:
        row["polarity"], row["expected_action"] = mapping[row["subtype"]]
    if row.get("fact_text") == "":
        row["fact_text"] = None
    return row


def item_schema(subtypes: list[str], extra: dict | None = None) -> dict:
    """Strict JSON schema for one instance; `extra` adds required string/enum properties (e.g. inject ops)."""
    props = {
        "subtype": {"type": "string", "enum": subtypes},
        "polarity": {"type": "string", "enum": ["change", "keep", "flag"]},
        "expected_action": {"type": "string", "enum": sorted(ACTIONS)},
        "target_text": {"type": "string"},
        "fact_text": {"type": ["string", "null"]},
        "notes": {"type": "string"},
    }
    props.update(extra or {})
    return {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}


def list_format(name: str, key: str, item: dict) -> dict:
    """Wrap an item schema as a strict response_format for {key: [item, ...]}."""
    return {"type": "json_schema", "json_schema": {"name": name, "strict": True, "schema": {
        "type": "object", "properties": {key: {"type": "array", "items": item}},
        "required": [key], "additionalProperties": False}}}
