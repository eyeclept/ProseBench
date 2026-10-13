"""Catalog native rule instances in each untouched source passage.

One Grok call per (passage, rule) with a strict JSON schema, then at most one
batched repair call for every item that fails validation. Items still invalid
after that repair are dropped and logged. Each rule's validated result is cached
in out/P{n}/inventory_R{rule}.json so a rerun skips finished rules.

Rule 4 coverage: any non-ASCII character left uncovered after the Rule 4 call
and its repair gets a deterministic `other` instance with expected_action
`ascii_equivalent` and a note marking it for owner review in the audit worksheet.
"""

import argparse
import json
import logging

from bench.corpus.common import (OUT, REQUIRED, SOURCE, item_schema, list_format, normalize, parse_json,
                                 rules_text, source_text, validate_instance)
from bench.corpus.coverage import uncovered
from bench.llm_clients import grok_chat

logger = logging.getLogger(__name__)


def _instruction(passage: str, rule: int, text: str) -> str:
    return (
        f"Inventory EVERY native instance of rule {rule} in the complete essay below. Catalogue ONLY violations "
        f"of rule {rule}; ignore violations of the other four rules"
        + (", including non-keyboard characters, which rule 4 covers" if rule != 4 else "")
        + ". The other rules are included only so you classify against the right rule."
        + (" Every rule 1 instance must contain a word or phrase from the banned words list."
           if rule == 1 else "")
        + " If a hit fits none of the named subtypes, use subtype 'other' and explain it in notes. "
        "Do not invent text.\n"
        "- target_text: a verbatim substring of the essay that occurs exactly once. Use the smallest complete "
        "clause or phrase containing the violation. Copy every character exactly, including Unicode.\n"
        "- For non-keyboard characters, group neighboring occurrences into one excerpt when they share one "
        "correction. Cover every occurrence, including non-breaking spaces and hyphens and subscripts. A "
        "correctly spelled name with a diacritic is subtype 'diacritic' (keep), not a violation.\n"
        "- fact_text: for replace_with_fact, a verbatim substring elsewhere in the essay holding the supporting "
        "number; otherwise null.\n"
        f"Subtype -> (polarity, expected_action) for rule {rule}: {json.dumps(REQUIRED[rule])}. "
        "For subtype 'other' pick polarity and expected_action from the allowed values.\n\n"
        f"Frozen rules:\n{rules_text()}\n\nComplete source essay ({passage}):\n{text}"
    )


def _validate(rows: list[dict], passage: str, rule: int, text: str) -> tuple[list[dict], list[tuple[dict, str]]]:
    good, bad = [], []
    for row in rows:
        row = normalize(dict(row, passage=passage, rule=rule, kind="native"))
        try:
            validate_instance(row, text)
        except (TypeError, ValueError, KeyError) as exc:
            logger.warning("Invalid native item %s R%d: %s", passage, rule, exc)
            bad.append((row, str(exc)))
            continue
        good.append(row)
    return good, bad


def _dedupe(rows: list[dict]) -> list[dict]:
    seen, out = set(), []
    for row in rows:
        if row["target_text"] not in seen:
            seen.add(row["target_text"])
            out.append(row)
    return out


def _rule4_fill(text: str, rows: list[dict], passage: str) -> list[dict]:
    """Deterministic coverage for non-ASCII characters the model missed."""
    filled = []
    for index in uncovered(text, rows + filled):
        width = 6
        while True:
            start, end = max(0, index - width), min(len(text), index + width + 1)
            snippet = text[start:end]
            if text.count(snippet) == 1 or (start == 0 and end == len(text)):
                break
            width += 6
        overlap = [r for r in filled if r["target_text"] in snippet or snippet in r["target_text"]]
        if overlap:
            continue
        row = {"passage": passage, "rule": 4, "kind": "native", "polarity": "change", "subtype": "other",
               "expected_action": "ascii_equivalent", "target_text": snippet, "fact_text": None,
               "notes": f"auto-filled for U+{ord(text[index]):04X}; model did not catalogue it; owner to review"}
        validate_instance(row, text)
        filled.append(row)
    return filled


def inventory_rule(passage: str, rule: int, text: str) -> list[dict]:
    directory = OUT / passage
    cache = directory / f"inventory_R{rule}.json"
    if cache.exists():
        return json.loads(cache.read_text(encoding="utf-8"))
    subtypes = list(REQUIRED[rule]) + ["other"]
    fmt = list_format(f"inventory_r{rule}", "instances", item_schema(subtypes))
    instruction = _instruction(passage, rule, text)
    reply = grok_chat([{"role": "user", "content": instruction}], reasoning_effort="medium", max_tokens=16000,
                      response_format=fmt, log_path=directory / f"inventory_R{rule}_raw.json")
    good, bad = _validate(parse_json(reply["content"])["instances"], passage, rule, text)
    if bad:
        listing = json.dumps([{"item": row, "error": err} for row, err in bad], ensure_ascii=False)
        repair = grok_chat(
            [{"role": "user", "content": instruction + "\n\nThese inventory items failed validation. Return a "
              "corrected version of each one you can fix. Copy target_text character-for-character from the "
              "essay and make it long enough to be unique. Omit any item that is not a real violation.\n"
              + listing}],
            reasoning_effort="low", max_tokens=8000, response_format=fmt,
            log_path=directory / f"inventory_R{rule}_repair_raw.json")
        fixed, still_bad = _validate(parse_json(repair["content"])["instances"], passage, rule, text)
        for row, err in still_bad:
            logger.warning("Dropping unrepaired native item %s R%d %r: %s", passage, rule,
                           row.get("target_text", "")[:80], err)
        good += fixed
    good = _dedupe(good)
    if rule == 4:
        filled = _rule4_fill(text, good, passage)
        if filled:
            logger.warning("%s R4: auto-filled %d uncovered non-ASCII snippets", passage, len(filled))
        good += filled
    cache.write_text(json.dumps(good, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return good


def inventory(passage: str) -> list[dict]:
    text = source_text(passage)
    directory = OUT / passage
    directory.mkdir(parents=True, exist_ok=True)
    results = []
    for rule in REQUIRED:
        rows = inventory_rule(passage, rule, text)
        results += rows
        print(f"{passage} R{rule}: {len(rows)} native instances", flush=True)
    # A target claimed by two rules is fine; identical target_text across rules would break span lookup only if
    # the text is non-unique, which validate_instance already rejects.
    missing = uncovered(text, results)
    if missing:
        raise ValueError(f"{passage}: {len(missing)} non-ASCII characters still uncovered: {missing[:40]}")
    (directory / "inventory.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n",
                                              encoding="utf-8")
    return results


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("passages", nargs="*", choices=list(SOURCE), default=list(SOURCE))
    args = parser.parse_args()
    for passage in args.passages:
        inventory(passage)


if __name__ == "__main__":
    main()
