"""Apply ordered edits while retaining original-passage span provenance."""

import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class EditSpan:
    index: int
    status: str
    original_start: int | None
    original_end: int | None
    revised_start: int | None
    revised_end: int | None
    original: str
    replacement: str | None

    def overlaps(self, start: int, end: int) -> bool:
        return (self.original_start is not None and
                self.original_start < end and start < self.original_end)


@dataclass
class AppliedText:
    text: str
    edit_spans: list[EditSpan]
    provenance: list[tuple[int, int]]

    def region(self, start: int, end: int) -> str:
        """Return the current text traced to an original half-open span."""
        positions = [i for i, (a, b) in enumerate(self.provenance)
                     if a < end and start < b]
        if positions:
            return self.text[positions[0]:positions[-1] + 1]
        return ""


def apply_edits(passage: str, edits: list[dict]) -> AppliedText:
    """Use the first current occurrence; span coordinates always refer to the input."""
    text = passage
    provenance = [(i, i + 1) for i in range(len(passage))]
    spans = []
    for index, edit in enumerate(edits):
        original = edit["original"]
        replacement = edit["replacement"]
        if not isinstance(original, str) or not original or (replacement is not None and not isinstance(replacement, str)):
            spans.append(EditSpan(index, "invalid", None, None, None, None, str(original), replacement))
            continue
        pos = text.find(original)
        if pos < 0:
            spans.append(EditSpan(index, "invalid", None, None, None, None, original, replacement))
            continue
        source = provenance[pos:pos + len(original)]
        start = min(a for a, _ in source)
        end = max(b for _, b in source)
        ambiguous = text.find(original, pos + 1) >= 0
        if replacement is None:
            spans.append(EditSpan(index, "ambiguous_flag" if ambiguous else "flag", start, end,
                                  pos, pos + len(original), original, None))
            continue
        spans.append(EditSpan(index, "ambiguous_applied" if ambiguous else "applied", start, end,
                              pos, pos + len(replacement), original, replacement))
        text = text[:pos] + replacement + text[pos + len(original):]
        provenance[pos:pos + len(original)] = [(start, end)] * len(replacement)
    return AppliedText(text, spans, provenance)
