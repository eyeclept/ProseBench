"""Assemble the single-rule prompts and their content hashes."""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Prompt:
    system: str
    user: str
    rule_text: str
    passage: str
    system_prompt_sha256: str
    prompt_sha256: str
    rule_text_sha256: str
    passage_sha256: str


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def assemble(root: Path, rule: int, passage_id: str, framing: str = "verbatim") -> Prompt:
    if rule not in range(1, 6) or framing not in ("verbatim", "easy"):
        raise ValueError("Invalid rule or framing")
    if rule != 3 and framing == "easy":
        raise ValueError("Easy framing applies only to rule 3")
    if passage_id not in ("P1", "P2", "P3"):
        raise ValueError("Invalid passage ID")
    prompts = root / "bench" / "prompts"
    rules = root / "bench" / "rules"
    system = (prompts / "system.md").read_text(encoding="utf-8")
    template = (prompts / "rule_call.md").read_text(encoding="utf-8")
    rule_text = (rules / f"rule{rule}.md").read_text(encoding="utf-8")
    passage = (root / "bench" / "corpus" / "out" / passage_id / "injected.md").read_text(encoding="utf-8")
    reference_block = ""
    if rule == 1:
        reference = (rules / "banned-words-phrases.md").read_text(encoding="utf-8")
        reference_block = '\n<reference name="banned-words-phrases.md">\n' + reference + '\n</reference>\n'
    framing_addendum = ""
    if rule == 3 and framing == "easy":
        framing_addendum = (prompts / "rule3_easy_addendum.md").read_text(encoding="utf-8")
    user = template
    for placeholder, value in (
        ("rule_text", rule_text),
        ("reference_block", reference_block),
        ("framing_addendum", framing_addendum),
        ("passage", passage),
    ):
        user = user.replace("{" + placeholder + "}", value)
    return Prompt(system, user, rule_text, passage, sha256(system), sha256(user), sha256(rule_text), sha256(passage))
