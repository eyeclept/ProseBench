"""Ask Grok for missing subtype insertions and apply only declared text operations.

Per (passage, rule): compute subtypes the inventory did not supply, ask Grok for
one structured op per missing subtype (strict JSON schema), apply the ops in
Python so untouched text stays byte-identical, and validate every native and
planted instance against the new text. On failure, re-ask once with the exact
error; a second failure raises. Progress is checkpointed per rule in
out/P{n}/inject_state.json, so a rerun resumes after the last finished rule.
"""

import argparse
import difflib
import json
import logging

from bench.corpus.common import (OUT, REQUIRED, SOURCE, item_schema, list_format, normalize, parse_json,
                                 rules_text, source_text, validate_instance)
from bench.llm_clients import grok_chat

logger = logging.getLogger(__name__)

OP_FIELDS = {
    "anchor_text": {"type": "string"},
    "op": {"type": "string", "enum": ["insert_after", "replace"]},
    "new_text": {"type": "string"},
}


def apply_ops(text: str, ops: list[dict]) -> str:
    """Apply unique, non-overlapping anchors and reject undeclared edits."""
    for op in ops:
        anchor = op["anchor_text"]
        new = op["new_text"]
        if not isinstance(anchor, str) or not anchor or text.count(anchor) != 1 or not isinstance(new, str):
            raise ValueError(f"Missing/nonunique edit anchor: {repr(anchor)[:100]}")
        if op["op"] not in ("insert_after", "replace"):
            raise ValueError(f"Unsupported edit operation: {op['op']}")
        pos = text.index(anchor)
        if op["op"] == "insert_after":
            if not new.startswith((" ", "\n")):
                raise ValueError("Inserted text must start with a separator")
            pos += len(anchor)
            text = text[:pos] + new + text[pos:]
        else:
            text = text[:pos] + new + text[pos + len(anchor):]
    return text


def _prompt(passage: str, rule: int, missing: list[str], natives: list[dict], text: str) -> str:
    mapping = REQUIRED[rule]
    return (
        f"In the {passage} essay below, plant EXACTLY ONE example of each missing subtype of rule {rule}: "
        + json.dumps({s: mapping[s] for s in missing})
        + ". Plant must-not-change (keep/flag) instances before change instances.\n"
        "- Each op inserts ONE new sentence (insert_after an existing anchor) or replaces ONE existing sentence. "
        "Prefer insert_after. Keep the essay's topic, citations, and voice.\n"
        "- anchor_text: an exact substring already in the essay that occurs once. It must not contain or "
        "overlap any native inventory target listed below.\n"
        "- new_text: the exact inserted or replacement text. For insert_after, start it with a space or newline.\n"
        "- target_text: the exact substring of new_text that carries the instance. It must occur exactly once "
        "in the resulting essay. new_text must not repeat any native target string.\n"
        "- One instance per op and no other unlabelled violation of rules 1-5 in new_text.\n"
        "- fact_available (R1) and number_available (R5): the supporting number must appear in the essay outside "
        "target_text. You may state it in a separate sentence inside new_text; put that number-bearing substring "
        "in fact_text. no_fact (R1) and no_number (R5): no number anywhere supports the claim; fact_text null.\n"
        "- Rule 4: use the real Unicode characters (U+2014 em dash, U+2013 en dash, U+201C/U+201D curly quotes, "
        "U+2026 ellipsis) and, for diacritic, a correctly spelled word or name with a real diacritic such as "
        "caf\u00e9 (U+00E9).\n"
        "- Rule 3 ambiguous: a trailing 'not X' / 'rather than X' where it is genuinely unclear whether X is "
        "ordinary general knowledge, so the right move is to ask the author.\n"
        f"Subtype -> (polarity, expected_action): {json.dumps(mapping)}\n\n"
        f"Frozen rules:\n{rules_text()}\n\nExisting native inventory for rule {rule}:\n"
        + json.dumps([{k: r[k] for k in ('subtype', 'target_text')} for r in natives if r["rule"] == rule],
                     ensure_ascii=False)
        + f"\n\nCurrent essay:\n{text}"
    )


def _attempt(passage: str, rule: int, missing: list[str], ops: list[dict], text: str,
             existing: list[dict]) -> tuple[str, list[dict]]:
    new_text = apply_ops(text, ops)
    additions = [normalize({"passage": passage, "rule": rule, "kind": "planted", "subtype": op["subtype"],
                            "polarity": op["polarity"], "expected_action": op["expected_action"],
                            "target_text": op["target_text"], "fact_text": op["fact_text"],
                            "notes": op["notes"]}) for op in ops]
    if sorted(r["subtype"] for r in additions) != sorted(missing):
        raise ValueError(f"expected one op per subtype {missing}, got {[r['subtype'] for r in additions]}")
    for op, row in zip(ops, additions):
        if row["target_text"] not in op["new_text"]:
            raise ValueError(f"target_text {row['target_text'][:80]!r} is not inside its new_text")
    for row in existing + additions:
        validate_instance(row, new_text)
    return new_text, additions


def inject(passage: str) -> list[dict]:
    directory = OUT / passage
    natives = json.loads((directory / "inventory.json").read_text(encoding="utf-8"))
    original = source_text(passage)
    state_path = directory / "inject_state.json"
    if state_path.exists():
        state = json.loads(state_path.read_text(encoding="utf-8"))
    else:
        state = {"done_rules": [], "text": original, "planted": [], "declared": []}
    for rule, mapping in REQUIRED.items():
        if rule in state["done_rules"]:
            continue
        text, planted = state["text"], state["planted"]
        present = {row["subtype"] for row in natives + planted if row["rule"] == rule}
        missing = sorted((s for s in mapping if s not in present), key=lambda s: (mapping[s][0] == "change", s))
        ops: list[dict] = []
        if missing:
            fmt = list_format(f"inject_r{rule}", "ops", item_schema(missing, OP_FIELDS))
            messages = [{"role": "user", "content": _prompt(passage, rule, missing, natives, text)}]
            for attempt in (1, 2):
                reply = grok_chat(messages, reasoning_effort="medium", max_tokens=8000, response_format=fmt,
                                  log_path=directory / f"inject_R{rule}_try{attempt}_raw.json")
                ops = parse_json(reply["content"])["ops"]
                try:
                    text, additions = _attempt(passage, rule, missing, ops, text, natives + planted)
                    break
                except (TypeError, ValueError, KeyError) as exc:
                    logger.warning("%s R%d injection attempt %d failed: %s", passage, rule, attempt, exc)
                    if attempt == 2:
                        raise ValueError(f"{passage} R{rule}: injection failed twice; last error: {exc}") from exc
                    messages += [{"role": "assistant", "content": reply["content"]},
                                 {"role": "user", "content": f"Those ops failed validation: {exc}. Return a "
                                  "corrected full ops list for the same missing subtypes, against the same "
                                  "current essay."}]
            planted.extend(additions)
            state["declared"].extend(ops)
            print(f"{passage} R{rule}: planted {', '.join(missing)}", flush=True)
        else:
            print(f"{passage} R{rule}: inventory already covers every subtype", flush=True)
        state.update(text=text, planted=planted)
        state["done_rules"].append(rule)
        state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    text = state["text"]
    if apply_ops(original, state["declared"]) != text:
        raise ValueError(f"Undeclared change in {passage} injected essay")
    (directory / "injected.md").write_text(text, encoding="utf-8")
    (directory / "planted.json").write_text(json.dumps(state["planted"], ensure_ascii=False, indent=2) + "\n",
                                            encoding="utf-8")
    diff = difflib.unified_diff(original.splitlines(keepends=True), text.splitlines(keepends=True),
                                fromfile="source.md", tofile="injected.md")
    (directory / "injection.diff").write_text("".join(diff), encoding="utf-8")
    (directory / "operations.json").write_text(json.dumps(state["declared"], ensure_ascii=False, indent=2) + "\n",
                                               encoding="utf-8")
    return state["planted"]


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("passages", nargs="*", choices=list(SOURCE), default=list(SOURCE))
    args = parser.parse_args()
    for passage in args.passages:
        inject(passage)


if __name__ == "__main__":
    main()
