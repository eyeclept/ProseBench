"""Compare hand-scored owner labels with scorer labels using Cohen's kappa."""

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)
KEY = ["model_key", "run_id", "instance_id"]


def cohen_kappa(owner: pd.Series, scorer: pd.Series) -> float:
    """Calculate nominal-label Cohen's kappa from paired labels."""
    if len(owner) != len(scorer) or not len(owner):
        raise ValueError("Kappa requires at least one paired label")
    categories = sorted(set(owner) | set(scorer))
    observed = float((owner.to_numpy() == scorer.to_numpy()).mean())
    expected = sum(float(owner.eq(label).mean() * scorer.eq(label).mean()) for label in categories)
    if expected == 1:
        return float("nan")
    return (observed - expected) / (1 - expected)


def kappa_ci(owner: pd.Series, scorer: pd.Series, samples: int = 2000, seed: int = 645) -> tuple[float, float]:
    """Percentile bootstrap confidence interval over paired worksheet rows."""
    rng = np.random.default_rng(seed)
    left = owner.reset_index(drop=True)
    right = scorer.reset_index(drop=True)
    values = []
    for _ in range(samples):
        indexes = rng.integers(0, len(left), len(left))
        estimate = cohen_kappa(left.iloc[indexes], right.iloc[indexes])
        if np.isfinite(estimate):
            values.append(estimate)
    if not values:
        return float("nan"), float("nan")
    return tuple(float(value) for value in np.percentile(values, (2.5, 97.5)))


def agreement(worksheet: Path, instances: Path) -> pd.DataFrame:
    """Join the worksheet to scorer labels and calculate each rule plus overall."""
    sheet = pd.read_csv(worksheet, dtype=str, keep_default_na=False)
    scored = pd.read_csv(instances, dtype=str, keep_default_na=False)
    sheet_fields = set(KEY + ["rule", "owner_label", "polarity"])
    scored_fields = set(KEY + ["rule", "label"])
    for path, frame, fields in ((worksheet, sheet, sheet_fields), (instances, scored, scored_fields)):
        missing = fields - set(frame.columns)
        if missing:
            raise ValueError(f"{path} missing columns: {sorted(missing)}")
    if sheet.duplicated(KEY).any() or scored.duplicated(KEY).any():
        raise ValueError("Duplicate worksheet or scorer identity")
    if sheet.owner_label.eq("").any():
        raise ValueError("Worksheet contains unscored owner_label cells")
    joined = sheet.merge(scored[KEY + ["rule", "label"]], on=KEY, how="left",
                         validate="one_to_one", suffixes=("_owner", "_scorer"), indicator=True)
    if not joined._merge.eq("both").all():
        raise ValueError("Worksheet includes rows absent from scorer CSV")
    if not joined.rule_owner.eq(joined.rule_scorer).all():
        raise ValueError("Rule mismatch between worksheet and scorer")
    conversions = {"correct": {"keep": "TN", "change": "TP", "flag": "TP"},
                   "incorrect": {"keep": "FP", "change": "FN", "flag": "FN"}}
    normalized = []
    for row in joined.itertuples():
        value = row.owner_label.strip()
        if value.lower() in conversions:
            value = conversions[value.lower()].get(row.polarity, "")
        normalized.append(value)
    joined["owner"] = normalized
    if not joined.owner.isin(("TP", "FN", "FP", "TN")).all() or not joined.label.isin(("TP", "FN", "FP", "TN")).all():
        raise ValueError("Labels must be TP/FN/FP/TN or owner correct/incorrect")
    rows = []
    for rule, group in [("overall", joined), *list(joined.groupby("rule_owner", sort=True))]:
        score = cohen_kappa(group.owner, group.label)
        low, high = kappa_ci(group.owner, group.label)
        rows.append(dict(rule=rule, n=len(group), kappa=score, ci_low=low, ci_high=high,
                         result="PASS" if score >= 0.7 else "FAIL"))
    return pd.DataFrame(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worksheet", type=Path, required=True)
    parser.add_argument("--instances", type=Path, default=Path("scores/instances.csv"))
    args = parser.parse_args()
    result = agreement(args.worksheet, args.instances)
    print(result.to_string(index=False, na_rep="NA", float_format=lambda value: f"{value:.4f}"))


if __name__ == "__main__":
    main()
