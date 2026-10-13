"""Compare the scorer (deterministic checks + Grok judge) with two blind AI raters (Grok 4.6, GPT-6.1 Sol).

Inputs: scores/instances.csv (scorer labels) and scores/ai_ratings_<rater>.csv (correct/incorrect per
instance, from bench.score.ai_rater). Rater verdicts map to TP/FN/FP/TN by polarity, as in kappa.py.
Output: Cohen's kappa with a bootstrap 95% CI and raw percent agreement for each pair, overall and per
rule, plus per-model recall under each labeler so ranking shifts are visible.
"""

import argparse
import logging
from pathlib import Path

import pandas as pd

from bench.analysis.kappa import cohen_kappa, kappa_ci

logger = logging.getLogger(__name__)
KEY = ["model_key", "run_id", "instance_id"]
CONVERT = {"correct": {"keep": "TN", "change": "TP", "flag": "TP"},
           "incorrect": {"keep": "FP", "change": "FN", "flag": "FN"}}
ORDER = ["qwen36", "qwen38flash", "mistral_small4", "glm53flash", "mimo26pro", "mistral_large4",
         "haiku55", "sonnet55", "opus55", "qwen36_high", "qwen38flash_high", "mistral_small4_high",
         "glm53flash_high", "mimo26pro_high", "mistral_large4_high", "haiku55_high", "sonnet55_high",
         "opus55_high"]


def _rater_labels(path: Path, name: str) -> pd.DataFrame:
    frame = pd.read_csv(path, dtype=str, keep_default_na=False)
    missing = frame.owner_label.eq("").sum()
    if missing:
        logger.warning("%s: %d unrated rows excluded", path, missing)
    frame = frame[frame.owner_label.ne("")]
    frame[name] = [CONVERT[v][p] for v, p in zip(frame.owner_label, frame.polarity)]
    return frame[KEY + [name]]


def load(scores: Path) -> pd.DataFrame:
    scored = pd.read_csv(scores / "instances.csv", dtype=str, keep_default_na=False)
    joined = scored[KEY + ["rule", "polarity"]].assign(scorer=scored.label)
    for name in ("grok", "gpt"):
        joined = joined.merge(_rater_labels(scores / f"ai_ratings_{name}.csv", name), on=KEY, how="inner",
                              validate="one_to_one")
    return joined


def agreement_table(joined: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for a, b in (("grok", "gpt"), ("scorer", "grok"), ("scorer", "gpt")):
        for rule, group in [("all", joined), *joined.groupby("rule", sort=True)]:
            low, high = kappa_ci(group[a], group[b])
            rows.append({"pair": f"{a} vs {b}", "rule": rule, "n": len(group),
                         "agreement": round(float((group[a] == group[b]).mean()), 3),
                         "kappa": round(cohen_kappa(group[a], group[b]), 3),
                         "ci_low": round(low, 3), "ci_high": round(high, 3)})
    return pd.DataFrame(rows)


def recall_table(joined: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for model in ORDER:
        group = joined[joined.model_key == model]
        if group.empty:
            continue
        row = {"model": model}
        for name in ("scorer", "grok", "gpt"):
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
    agree, recall = agreement_table(joined), recall_table(joined)
    text = (f"# Rater agreement\n\nRows rated by both raters: {len(joined)}\n\n"
            + agree.to_markdown(index=False) + "\n\n## Recall by labeler\n\n" + recall.to_markdown(index=False) + "\n")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(text, encoding="utf-8")
    print(text)


if __name__ == "__main__":
    main()
