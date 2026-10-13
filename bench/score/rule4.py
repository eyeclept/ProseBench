"""Check keyboard substitutions and heuristic comma-splice regressions."""

import logging
import re
import unicodedata

logger = logging.getLogger(__name__)

# Heuristic only: recognizes explicit subjects and a short list of finite verbs.
# It misses implicit subjects, unusual verb forms, and long or nested clauses;
# quotations and parentheticals can produce false positives.
_SUBJECT = r"(?:I|you|he|she|it|we|they|this|that|these|those|the\s+\w+|a\s+\w+|an\s+\w+)"
_VERB = r"(?:is|are|was|were|am|has|have|had|do|does|did|will|can|could|would|should|may|might|must|\w+ed|\w+s)"
_CLAUSE = re.compile(rf"\b{_SUBJECT}\s+(?:\w+\s+){{0,3}}{_VERB}\b", re.IGNORECASE)
_COMMA = re.compile(r",[\t ]*(?!and\b|but\b|or\b|so\b|yet\b|for\b|nor\b)([^,;.!?\n]+)", re.IGNORECASE)


def comma_splice_count(text: str) -> int:
    """Count likely bare commas between subject-and-verb clauses."""
    count = 0
    for match in _COMMA.finditer(text):
        before = re.split(r"[.;!?\n]", text[:match.start()])[-1]
        if _CLAUSE.search(before) and _CLAUSE.search(match.group(1)):
            count += 1
    return count


def keyboard_violations(text: str, provenance: list[tuple[int, int]],
                        protected: list[dict], original: str) -> list[dict]:
    """List non-ASCII characters except unchanged protected diacritics."""
    output = []
    for index, char in enumerate(text):
        if ord(char) < 128:
            continue
        a, b = provenance[index]
        protected_char = any(row["char_start"] <= a and b <= row["char_end"]
                             and char in original[a:b] for row in protected)
        if not protected_char:
            output.append({"offset": index, "codepoint": f"U+{ord(char):04X}",
                           "name": unicodedata.name(char, "UNKNOWN")})
    return output

def check_instance(row: dict, after: str, passage_before: str, passage_after: str,
                   split_context: str) -> list[str]:
    """Return failure flags for an edited Rule 4 target."""
    target = row["target_text"]
    action = row["expected_action"]
    failures = []
    if action == "keep":
        if target not in after:
            failures.append("diacritic_changed")
        return failures
    if any(ord(c) > 127 for c in after):
        failures.append("nonkeyboard_remains")
    punctuation = {
        "punct_semicolon_or_period": lambda value: ";" in value or "." in value,
        "punct_comma": lambda value: "," in value,
        "punct_split": lambda value: bool(re.search(r"[.!?][ \t]+[A-Z]", split_context)),
        "punct_hyphen": lambda value: "-" in value,
        "punct_straight_quote": lambda value: ('"' in value if any(c in target for c in '\u201c\u201d') else "'" in value),
        "punct_three_periods": lambda value: "..." in value,
        "ascii_equivalent": lambda value: bool(value.strip()) and value.isascii(),
    }
    if action not in punctuation or not punctuation[action](after):
        failures.append("wrong_punctuation_class")
    if comma_splice_count(passage_after) > comma_splice_count(passage_before):
        failures.append("comma_splice_introduced")
    return failures
