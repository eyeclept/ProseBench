"""Compare the scorer (deterministic checks + Grok judge) with three blind AI raters: Grok 4.6, GPT-6.1 Sol, Jev 1.13.

Inputs: scores/instances.csv (scorer labels) and scores/ai_ratings_<rater>.csv (correct/incorrect per instance,
from bench.score.ai_rater). Rater verdicts map to TP/FN/FP/TN by polarity, as in kappa.py.

Reference label: the Grok and GPT verdict where they agree. Where they split, Jev decides only when confident
(P(correct) <= 0.1 or >= 0.9); otherwise the item is unresolved and left out of scorer-vs-reference rows. On the
full matrix Jev's confident verdicts matched the Grok+GPT consensus 94-100% on every rule, while its uncertain
verdicts matched 53% on Rule 1 and 37% on Rule 3, so an uncertain vote is not evidence.

Output: Cohen's kappa (bootstrap 95% CI) and percent agreement for each pair, overall and per rule; tie-break
counts; Jev agreement with the Grok+GPT consensus by Jev confidence; per-model recall under each labeler.
"""

import argparse
import logging
import re
from pathlib import Path

import pandas as pd

from bench.analysis.kappa import cohen_kappa, kappa_ci

logger = logging.getLogger(__name__)
KEY = ["model_key", "run_id", "instance_id"]
RATERS = ("grok", "gpt", "jev")
LABELERS = ("scorer", *RATERS, "reference")
PAIRS = (("grok", "gpt"), ("grok", "jev"), ("gpt", "jev"),
         ("scorer", "grok"), ("scorer", "gpt"), ("scorer", "jev"), ("scorer", "reference"))
CONVERT = {"correct": {"keep": "TN", "change": "TP", "flag": "TP"},
           "incorrect": {"keep": "FP", "change": "FN", "flag": "FN"}}
CONFIDENT = 0.4  # Jev counts as confident when |P(correct) - 0.5| >= this, i.e. P <= 0.1 or P >= 0.9.
ORDER = ["qwen36", "qwen38flash", "mistral_small4", "glm53flash", "mimo26pro", "mistral_large4",
         "haiku55", "sonnet55", "opus55", "qwen36_high", "qwen38flash_high", "mistral_small4_high",
         "glm53flash_high", "mimo26pro_high", "mistral_large4_high", "haiku55_high", "sonnet55_high",
         "opus55_high"]


def _rater_labels(path: Path, name: str) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = frame.owner_label.eq("").sum()
    if missing:
        logger.warning("%s: %d unrated rows excluded", path, missing)
    frame = frame[frame.owner_label.ne("")].copy()
    frame[name] = [CONVERT[v][p] for v, p in zip(frame.owner_label, frame.polarity)]
    columns = KEY + [name]
    if name == "jev":
        frame["jev_p"] = [float(re.search(r"p_correct=([0-9.]+)", note).group(1)) for note in frame.owner_notes]
        columns.append("jev_p")
    return frame[columns]


def load(scores: Path) -> pd.DataFrame:
    scored = pd.read_csv(scores / "instances.csv", dtype=str, keep_default_na=False)
    joined = scored[KEY + ["rule", "polarity"]].assign(scorer=scored.label)
    for name in RATERS:
        joined = joined.merge(_rater_labels(scores / f"ai_ratings_{name}.csv", name), on=KEY, how="inner",
                              validate="one_to_one")
    joined["tie_break"] = joined.grok.ne(joined.gpt)
    jev_confident = (joined.jev_p - 0.5).abs() >= CONFIDENT
    joined["reference"] = joined.grok.where(~joined.tie_break, joined.jev.where(jev_confident, ""))
    return joined


def agreement_table(joined: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for a, b in PAIRS:
        for rule, group in [("all", joined), *joined.groupby("rule", sort=True)]:
            if "reference" in (a, b):
                group = group[group.reference.ne("")]
            low, high = kappa_ci(group[a], group[b])
            rows.append({"pair": f"{a} vs {b}", "rule": rule, "n": len(group),
                         "agreement": round(float((group[a] == group[b]).mean()), 3),
                         "kappa": round(cohen_kappa(group[a], group[b]), 3),
                         "ci_low": round(low, 3), "ci_high": round(high, 3)})
    return pd.DataFrame(rows)


def tie_break_table(joined: pd.DataFrame) -> pd.DataFrame:
    """How many reference labels rest on Jev's vote, and whom Jev sided with."""
    rows = []
    for rule, group in [("all", joined), *joined.groupby("rule", sort=True)]:
        split = group[group.tie_break]
        decided = split[split.reference.ne("")]
        rows.append({"rule": rule, "n": len(group), "grok_gpt_split": len(split),
                     "split_share": round(len(split) / len(group), 4),
                     "jev_decided": len(decided), "unresolved": len(split) - len(decided),
                     "jev_sides_grok": int((decided.jev == decided.grok).sum()),
                     "jev_sides_gpt": int((decided.jev == decided.gpt).sum())})
    return pd.DataFrame(rows)


def confidence_table(joined: pd.DataFrame) -> pd.DataFrame:
    """Jev agreement with the Grok+GPT consensus, split by Jev confidence."""
    agreed = joined[~joined.tie_break]
    confident = (agreed.jev_p - 0.5).abs() >= CONFIDENT
    rows = []
    for bucket, group in (("confident (P<=0.1 or P>=0.9)", agreed[confident]), ("uncertain", agreed[~confident])):
        rows.append({"jev_bucket": bucket, "n": len(group), "share": round(len(group) / len(agreed), 3),
                     "agreement_with_consensus": round(float((group.jev == group.grok).mean()), 3)
                     if len(group) else None})
    return pd.DataFrame(rows)


def recall_table(joined: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model in ORDER:
        group = joined[joined.model_key == model]
        if group.empty:
            continue
        row = {"model": model}
        for name in LABELERS:
            tp, fn = (group[name] == "TP").sum(), (group[name] == "FN").sum()
            row[f"recall_{name}"] = round(tp / (tp + fn), 3) if tp + fn else None
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--scores", type=Path, default=Path("scores"))
    parser.add_argument("--out", type=Path, default=Path("analysis_out/rater_agreement.md"))
    args = parser.parse_args()
    joined = load(args.scores)
    text = (f"# Rater agreement\n\nRows rated by all three raters: {len(joined)}\n\n"
            "Reference = Grok and GPT verdict where they agree. On a split, Jev decides only when confident "
            "(P <= 0.1 or P >= 0.9); other splits are unresolved and excluded from scorer-vs-reference rows. "
            "All labels are automated; there is no human validation.\n\n## Pairwise agreement\n\n"
            + agreement_table(joined).to_markdown(index=False)
            + "\n\n## Tie-breaks (reference labels decided by Jev)\n\n" + tie_break_table(joined).to_markdown(index=False)
            + "\n\n## Jev agreement with the Grok+GPT consensus, by Jev confidence\n\n"
            + confidence_table(joined).to_markdown(index=False)
            + "\n\n## Recall by labeler\n\n" + recall_table(joined).to_markdown(index=False) + "\n")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
