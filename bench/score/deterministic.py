"""Apply fixed scoring rules and identify cases needing a human-like judge."""

import logging
import re

from bench.score.rule4 import check_instance

logger = logging.getLogger(__name__)

_NUMBER = re.compile(r"(?<![\w.])\d+(?:[.,]\d+)*%?(?!\w)")


def numbers(text: str) -> set[str]:
    """Return literal numeric tokens, including decimals and percentages."""
    return set(_NUMBER.findall(text))


def fabricated_numbers(passage: str, applied: object) -> list[str]:
    known = numbers(passage)
    return sorted({number for edit in applied.edit_spans
                   if edit.status in ("applied", "ambiguous_applied")
                   for number in numbers(edit.replacement or "") if number not in known})


def outcome(row: dict, spans: list) -> str:
    """Classify only edits whose original span meets the instance span."""
    touching = [item for item in spans if item.overlaps(row["char_start"], row["char_end"])]
    if any(item.status in ("applied", "ambiguous_applied") for item in touching):
        return "edited"
    if any(item.status in ("flag", "ambiguous_flag") for item in touching):
        return "flagged"
    return "untouched"


def collateral(spans: list, scored: list[dict], all_rows: list[dict]) -> list[dict]:
    """Count applied edits that miss the scored rule; flags are not edits."""
    output = []
    for item in spans:
        if item.status not in ("applied", "ambiguous_applied"):
            continue
        if any(item.overlaps(row["char_start"], row["char_end"]) for row in scored):
            continue
        category = ("other_rule_instance" if any(
            item.overlaps(row["char_start"], row["char_end"]) for row in all_rows)
            else "uncatalogued_text")
        output.append({"index": item.index, "category": category})
    return output


def assess(row: dict, state: str, original: str, revised: str, applied: object) -> tuple[str | None, list[str]]:
    """Return a fixed verdict or None for judge review, plus failure flags."""
    flags = []
    touched = [span for span in applied.edit_spans
               if span.overlaps(row["char_start"], row["char_end"])]
    for span in touched:
        if span.status.startswith("ambiguous"):
            flags.append("ambiguous_edit")
    if state == "untouched":
        return ("correct" if row["polarity"] == "keep" else "incorrect"), flags
    if row["polarity"] == "keep":
        if state == "flagged":
            return "incorrect", flags
        if row["rule"] == 1 and row["subtype"] == "technical_term" and row["target_text"] not in revised:
            return "incorrect", flags
        if row["rule"] == 4 and row["subtype"] == "diacritic":
            flags += check_instance(row, revised, original, applied.text, revised)
            if "diacritic_changed" in flags:
                return "incorrect", flags
        return None, flags
    if state == "flagged":
        return ("correct" if row["polarity"] == "flag" else "incorrect"), flags
    if row["polarity"] == "flag":
        return "incorrect", flags
    if row["expected_action"] == "replace_with_fact":
        fact = row.get("fact_text") or ""
        expected = numbers(fact)
        if not expected or not expected.issubset(numbers(revised)):
            flags.append("expected_number_missing")
            return "incorrect", flags
        if row["rule"] == 1 and row["target_text"] in revised:
            return "incorrect", flags
        return None, flags
    if row["rule"] == 1:
        if row["target_text"] in revised:
            return "incorrect", flags
        if row["expected_action"] == "cut":
            if all(span.replacement == "" for span in touched if span.status.endswith("applied")):
                return "correct", flags
            return None, flags
        return "correct", flags
    if row["rule"] == 4:
        split_context = revised + applied.region(row["char_end"], row["char_end"] + 1)
        flags += check_instance(row, revised, original, applied.text, split_context)
        return ("incorrect" if any(flag in flags for flag in
                ("wrong_punctuation_class", "nonkeyboard_remains", "comma_splice_introduced")) else "correct"), flags
    if row["expected_action"] == "promote_to_sentence":
        return None, flags
    if row["expected_action"] == "cut":
        if row["target_text"] in revised:
            return "incorrect", flags
        if all(span.replacement == "" for span in touched if span.status.endswith("applied")):
            return "correct", flags
        return None, flags
    return "incorrect", flags
