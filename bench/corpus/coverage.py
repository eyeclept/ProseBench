"""Check whether every native non-ASCII character is covered by a Rule 4 target."""

import logging

logger = logging.getLogger(__name__)


def uncovered(text: str, rows: list[dict]) -> list[int]:
    covered = bytearray(len(text))
    for row in rows:
        if row["rule"] != 4:
            continue
        target = row["target_text"]
        start = text.index(target)
        covered[start:start + len(target)] = bytes([1]) * len(target)
    return [index for index, char in enumerate(text) if ord(char) > 127 and not covered[index]]
