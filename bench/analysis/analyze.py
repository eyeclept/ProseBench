"""Analyze scored instance and run CSVs; write Markdown tables and PNG figures."""

import argparse
import logging
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from statsmodels.stats.contingency_tables import mcnemar
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint

logger = logging.getLogger(__name__)

INSTANCE_COLUMNS = {"run_id", "model_key", "rule", "passage", "repeat", "framing",
                    "instance_id", "kind", "polarity", "subtype", "outcome", "label",
                    "flags", "ordinary_cut", "field_specific_promoted", "ambiguous_flagged"}
RUN_COLUMNS = {"run_id", "model_key", "rule", "passage", "repeat", "framing",
               "cost_usd", "usage_output", "usage_reasoning", "parse_error",
               "invalid_edit_count", "firecrawl_called", "TP", "collateral_count",
               "other_rule_instance", "uncatalogued_text", "fabricated_numbers"}
BASE_MODELS = ("qwen36", "qwen38flash", "mistral_small4", "glm53flash", "mimo26pro",
               "mistral_large4", "haiku55", "sonnet55", "opus55")
MODELS = BASE_MODELS + tuple(f"{key}_high" for key in BASE_MODELS)
BASE_PAIRS = (("qwen36", "qwen38flash"), ("qwen38flash", "glm53flash"),
              ("mistral_small4", "glm53flash"), ("glm53flash", "mimo26pro"),
              ("glm53flash", "mistral_large4"), ("qwen36", "haiku55"),
              ("glm53flash", "sonnet55"), ("mimo26pro", "opus55"))
PAIRS = BASE_PAIRS + tuple((f"{left}_high", f"{right}_high") for left, right in BASE_PAIRS)
RUN_NUMERIC = ("cost_usd", "usage_output", "usage_reasoning", "invalid_edit_count", "TP",
               "collateral_count", "other_rule_instance", "uncatalogued_text")
KEY = ["model_key", "run_id"]
CELL = ["rule", "framing", "passage", "instance_id", "repeat"]


def wilson(successes: int, total: int) -> tuple[float, float]:
    """Return a Wilson interval, or missing endpoints when the denominator is zero."""
    if total == 0:
        return float("nan"), float("nan")
    low, high = proportion_confint(successes, total, alpha=0.05, method="wilson")
    return float(low), float(high)


def load_scores(scores: Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Read the scorer's exact CSV columns without treating empty strings as NA."""
    instances = pd.read_csv(scores / "instances.csv", dtype=str, keep_default_na=False)
    runs = pd.read_csv(scores / "runs.csv", dtype=str, keep_default_na=False)
    for name, frame, required in (("instances.csv", instances, INSTANCE_COLUMNS),
                                  ("runs.csv", runs, RUN_COLUMNS)):
        missing = required - set(frame.columns)
        if missing:
            raise ValueError(f"{name} missing columns: {sorted(missing)}")
    for frame in (instances, runs):
        frame["rule"] = pd.to_numeric(frame["rule"], errors="raise").astype(int)
        frame["repeat"] = pd.to_numeric(frame["repeat"], errors="raise").astype(int)
    for key in RUN_NUMERIC:
        runs[key] = pd.to_numeric(runs[key], errors="raise")
    for key in ("parse_error", "firecrawl_called"):
        normalized = runs[key].str.lower()
        if not normalized.isin(("true", "false")).all():
            raise ValueError(f"Invalid boolean in runs.csv: {key}")
        runs[key] = normalized.eq("true")
    if runs.duplicated(KEY).any() or instances.duplicated(KEY + ["instance_id"]).any():
        raise ValueError("Duplicate run or instance identity")
    if not instances["label"].isin(("TP", "FN", "FP", "TN")).all():
        raise ValueError("Invalid instance label")
    if not instances["kind"].isin(("native", "planted")).all():
        raise ValueError("Invalid instance kind")
    joined = instances.merge(runs[KEY], on=KEY, how="left", validate="many_to_one", indicator=True)
    if not joined["_merge"].eq("both").all():
        raise ValueError("Instance without matching run")
    for key in ("rule", "passage", "repeat", "framing"):
        expected = instances[KEY + [key]].merge(runs[KEY + [key]], on=KEY, validate="many_to_one", suffixes=("_instance", "_run"))
        if not expected[f"{key}_instance"].equals(expected[f"{key}_run"]):
            raise ValueError(f"Run metadata mismatch: {key}")
    return joined.drop(columns="_merge"), runs


def metrics(instances: pd.DataFrame) -> pd.DataFrame:
    """Count confusion labels, then calculate pooled precision, recall and F1."""
    rows = []
    for (rule, model), group in instances.groupby(["rule", "model_key"], sort=True):
        counts = group["label"].value_counts()
        tp, fn, fp, tn = (int(counts.get(label, 0)) for label in ("TP", "FN", "FP", "TN"))
        p = tp / (tp + fp) if tp + fp else float("nan")
        r = tp / (tp + fn) if tp + fn else float("nan")
        p_low, p_high = wilson(tp, tp + fp)
        r_low, r_high = wilson(tp, tp + fn)
        f1 = 2 * p * r / (p + r) if p + r > 0 else float("nan")
        rows.append(dict(rule=rule, model_key=model, TP=tp, FN=fn, FP=fp, TN=tn,
                         precision=p, precision_low=p_low, precision_high=p_high,
                         recall=r, recall_low=r_low, recall_high=r_high, f1=f1))
    return pd.DataFrame(rows, columns=["rule", "model_key", "TP", "FN", "FP", "TN",
                                        "precision", "precision_low", "precision_high",
                                        "recall", "recall_low", "recall_high", "f1"])


def rule3_rates(instances: pd.DataFrame) -> pd.DataFrame:
    """Measure each Rule 3 binary within each framing."""
    rows = []
    rule3 = instances[instances.rule == 3]
    for (model, framing), group in rule3.groupby(["model_key", "framing"]):
        for subtype, column in (("ordinary", "ordinary_cut"),
                                ("field_specific", "field_specific_promoted"),
                                ("ambiguous", "ambiguous_flagged")):
            values = group.loc[group.subtype == subtype, column]
            if values.empty:
                continue
            if not values.isin(("0", "1")).all():
                raise ValueError(f"Invalid Rule 3 binary: {column}")
            n = len(values)
            successes = int(values.astype(int).sum())
            low, high = wilson(successes, n)
            rows.append(dict(model_key=model, framing=framing, binary=column,
                             successes=successes, n=n, rate=successes / n, low=low, high=high))
    return pd.DataFrame(rows, columns=["model_key", "framing", "binary", "successes", "n", "rate", "low", "high"])


def collateral_rates(runs: pd.DataFrame) -> pd.DataFrame:
    """Average collateral counts per run, including each source split."""
    return runs.groupby(["rule", "model_key"], as_index=False)[
        ["collateral_count", "other_rule_instance", "uncatalogued_text"]].mean()


def native_planted(instances: pd.DataFrame) -> pd.DataFrame:
    """Compare recall on naturally occurring and injected positive instances."""
    positive = instances[instances.polarity != "keep"]
    counts = positive.groupby(["rule", "model_key", "kind", "label"]).size().unstack(fill_value=0)
    if counts.empty:
        return pd.DataFrame(columns=["rule", "model_key", "native_recall", "planted_recall", "gap_planted_minus_native"])
    counts["recall"] = counts.get("TP", 0) / (counts.get("TP", 0) + counts.get("FN", 0))
    pivot = counts["recall"].unstack("kind").reset_index()
    pivot = pivot.rename(columns={"native": "native_recall", "planted": "planted_recall"})
    for column in ("native_recall", "planted_recall"):
        if column not in pivot:
            pivot[column] = float("nan")
    pivot["gap_planted_minus_native"] = pivot.planted_recall - pivot.native_recall
    return pivot[["rule", "model_key", "native_recall", "planted_recall", "gap_planted_minus_native"]]


def run_flags(runs: pd.DataFrame) -> pd.DataFrame:
    """Report per-run error/tool rates, with fabrication limited to Rules 1 and 5."""
    rows = []
    for model, group in runs.groupby("model_key"):
        relevant = group[group.rule.isin((1, 5))]
        rows.append(dict(model_key=model, runs=len(group), fabricated_number_rate=(
            relevant.fabricated_numbers.ne("[]").mean() if len(relevant) else float("nan")),
            parse_error_rate=group.parse_error.mean(),
            invalid_edit_rate=group.invalid_edit_count.gt(0).mean(),
            firecrawl_call_rate=group.firecrawl_called.mean()))
    return pd.DataFrame(rows, columns=["model_key", "runs", "fabricated_number_rate",
                                       "parse_error_rate", "invalid_edit_rate", "firecrawl_call_rate"])


def repeat_stability(instances: pd.DataFrame) -> pd.DataFrame:
    """Count complete three-repeat instance cells with identical outcomes."""
    rows = []
    for (rule, model), group in instances.groupby(["rule", "model_key"]):
        cells = group.groupby(["framing", "passage", "instance_id"])["outcome"].agg(["size", "nunique"])
        complete = cells[cells["size"] == 3]
        rows.append(dict(rule=rule, model_key=model, complete_cells=len(complete),
                         stable_cells=int(complete["nunique"].eq(1).sum()),
                         stable_fraction=complete["nunique"].eq(1).mean() if len(complete) else float("nan")))
    return pd.DataFrame(rows)


def passage_spread(instances: pd.DataFrame) -> pd.DataFrame:
    """Show minimum and maximum passage-level positive recall over P1-P3."""
    positive = instances[instances.polarity != "keep"]
    per_passage = positive.groupby(["rule", "model_key", "passage"]).label.apply(lambda s: s.eq("TP").mean())
    return per_passage.groupby(["rule", "model_key"]).agg(recall_min="min", recall_max="max").reset_index()


def paired_tiers(instances: pd.DataFrame) -> pd.DataFrame:
    """Use matched instance/repeat correctness and Holm correction per rule."""
    source = instances.copy()
    source["correct"] = source.label.isin(("TP", "TN"))
    rows = []
    for rule, group in source.groupby("rule"):
        indexed = {model: part.set_index(CELL)["correct"] for model, part in group.groupby("model_key")}
        for left, right in PAIRS:
            if left not in indexed or right not in indexed:
                continue
            pair = indexed[left].to_frame("left").join(indexed[right].rename("right"), how="inner")
            if pair.empty:
                continue
            left_only = int((pair.left & ~pair.right).sum())
            right_only = int((~pair.left & pair.right).sum())
            p = float(mcnemar([[0, left_only], [right_only, 0]], exact=True).pvalue)
            rows.append(dict(rule=rule, left=left, right=right, matched=len(pair),
                             left_only_correct=left_only, right_only_correct=right_only, p_exact=p))
    frame = pd.DataFrame(rows, columns=["rule", "left", "right", "matched", "left_only_correct", "right_only_correct", "p_exact"])
    frame["p_holm"] = float("nan")
    for _, group in frame.groupby("rule"):
        frame.loc[group.index, "p_holm"] = multipletests(group.p_exact.to_numpy(), method="holm")[1]
    return frame


def cost_table(runs: pd.DataFrame) -> pd.DataFrame:
    """Aggregate cost, correct edits and reasoning tokens by model and rule."""
    grouped = runs.groupby(["rule", "model_key"], as_index=False).agg(
        runs=("run_id", "size"), total_cost_usd=("cost_usd", "sum"),
        TP=("TP", "sum"), reasoning_tokens=("usage_reasoning", "sum"))
    grouped["mean_cost_usd_per_run"] = grouped.total_cost_usd / grouped.runs
    grouped["cost_usd_per_correct_edit"] = grouped.total_cost_usd / grouped.TP.replace(0, float("nan"))
    return grouped


def order_model_keys(frame: pd.DataFrame) -> pd.DataFrame:
    """Keep roster order and skip keys that are absent from the frame."""
    present = set(frame["model_key"].astype(str))
    categories = [key for key in MODELS if key in present]
    extras = [key for key in frame["model_key"].astype(str).unique() if key not in MODELS]
    ordered = frame.copy()
    ordered["model_key"] = pd.Categorical(ordered["model_key"].astype(str),
                                          categories=categories + extras, ordered=True)
    return ordered


def _condition_stats(instances: pd.DataFrame, runs: pd.DataFrame) -> dict[str, float]:
    """Pool recall, keep-damage, failures, usage, and cost for one condition slice."""
    counts = instances["label"].value_counts()
    tp, fn = (int(counts.get(label, 0)) for label in ("TP", "FN"))
    recall = tp / (tp + fn) if tp + fn else float("nan")
    keep = instances[instances.polarity == "keep"]
    keep_counts = keep["label"].value_counts()
    keep_fp, keep_tn = int(keep_counts.get("FP", 0)), int(keep_counts.get("TN", 0))
    keep_damage = keep_fp / (keep_fp + keep_tn) if keep_fp + keep_tn else float("nan")
    cost = float(runs.cost_usd.sum()) if len(runs) else 0.0
    return dict(recall=recall, keep_damage_fp_rate=keep_damage,
                failed_runs=int(runs.parse_error.sum()) if len(runs) else 0,
                median_usage_output=float(runs.usage_output.median()) if len(runs) else float("nan"),
                median_usage_reasoning=float(runs.usage_reasoning.median()) if len(runs) else float("nan"),
                cost_usd=cost, cost_per_tp=cost / tp if tp else float("nan"))


def reasoning_effect(instances: pd.DataFrame, runs: pd.DataFrame) -> pd.DataFrame:
    """Compare min vs high reasoning on quality, usage, and API cost."""
    columns = ["model_key", "rule", "recall_min", "recall_high", "recall_delta",
               "keep_damage_fp_rate_min", "keep_damage_fp_rate_high",
               "failed_runs_min", "failed_runs_high",
               "median_usage_output_min", "median_usage_output_high",
               "median_usage_reasoning_min", "median_usage_reasoning_high",
               "cost_usd_min", "cost_usd_high", "cost_ratio",
               "cost_per_tp_min", "cost_per_tp_high"]
    present = set(instances.model_key.astype(str))
    pairs = [model for model in BASE_MODELS if model in present and f"{model}_high" in present]
    rows = []

    def add(model: str, rule, min_inst: pd.DataFrame, high_inst: pd.DataFrame,
            min_run: pd.DataFrame, high_run: pd.DataFrame) -> None:
        if min_inst.empty or high_inst.empty:
            return
        minimum = _condition_stats(min_inst, min_run)
        high = _condition_stats(high_inst, high_run)
        cost_ratio = high["cost_usd"] / minimum["cost_usd"] if minimum["cost_usd"] else float("nan")
        rows.append(dict(model_key=model, rule=rule,
                         recall_min=minimum["recall"], recall_high=high["recall"],
                         recall_delta=high["recall"] - minimum["recall"],
                         keep_damage_fp_rate_min=minimum["keep_damage_fp_rate"],
                         keep_damage_fp_rate_high=high["keep_damage_fp_rate"],
                         failed_runs_min=minimum["failed_runs"], failed_runs_high=high["failed_runs"],
                         median_usage_output_min=minimum["median_usage_output"],
                         median_usage_output_high=high["median_usage_output"],
                         median_usage_reasoning_min=minimum["median_usage_reasoning"],
                         median_usage_reasoning_high=high["median_usage_reasoning"],
                         cost_usd_min=minimum["cost_usd"], cost_usd_high=high["cost_usd"],
                         cost_ratio=cost_ratio,
                         cost_per_tp_min=minimum["cost_per_tp"], cost_per_tp_high=high["cost_per_tp"]))

    for model in pairs:
        high_key = f"{model}_high"
        min_inst = instances[instances.model_key.astype(str) == model]
        high_inst = instances[instances.model_key.astype(str) == high_key]
        min_run = runs[runs.model_key.astype(str) == model]
        high_run = runs[runs.model_key.astype(str) == high_key]
        shared = set(min_inst.rule) & set(high_inst.rule)
        add(model, "all", min_inst[min_inst.rule.isin(shared)], high_inst[high_inst.rule.isin(shared)],
            min_run[min_run.rule.isin(shared)], high_run[high_run.rule.isin(shared)])
    for model in pairs:
        high_key = f"{model}_high"
        min_inst = instances[instances.model_key.astype(str) == model]
        high_inst = instances[instances.model_key.astype(str) == high_key]
        min_run = runs[runs.model_key.astype(str) == model]
        high_run = runs[runs.model_key.astype(str) == high_key]
        for rule in sorted(set(min_inst.rule) & set(high_inst.rule)):
            add(model, rule, min_inst[min_inst.rule == rule], high_inst[high_inst.rule == rule],
                min_run[min_run.rule == rule], high_run[high_run.rule == rule])
    return pd.DataFrame(rows, columns=columns)



def routing(quality: pd.DataFrame, cost: pd.DataFrame, thresholds: tuple[float, ...]) -> pd.DataFrame:
    """Choose the cheapest qualifying model for each rule and threshold."""
    joined = quality.merge(cost[["rule", "model_key", "mean_cost_usd_per_run"]], on=["rule", "model_key"])
    rows = []
    for threshold in dict.fromkeys(thresholds):
        for rule, group in joined.groupby("rule"):
            eligible = group[(group.precision_low >= threshold) & (group.recall_low >= threshold)]
            if eligible.empty:
                rows.append(dict(threshold=threshold, rule=rule, model_key="None qualifies",
                                 mean_cost_usd_per_run=float("nan"), precision_low=float("nan"), recall_low=float("nan")))
                continue
            choice = eligible.sort_values(["mean_cost_usd_per_run", "model_key"]).iloc[0]
            rows.append(dict(threshold=threshold, rule=rule, model_key=choice.model_key,
                             mean_cost_usd_per_run=choice.mean_cost_usd_per_run,
                             precision_low=choice.precision_low, recall_low=choice.recall_low))
    return pd.DataFrame(rows)


def write_table(out: Path, name: str, frame: pd.DataFrame, note: str = "") -> None:
    """Write a plain Markdown table, including a heading when empty."""
    columns = list(frame.columns)
    lines = [f"# {name}", ""]
    if note:
        lines.extend((note, ""))
    lines.extend(("| " + " | ".join(columns) + " |",
                  "| " + " | ".join("---" for _ in columns) + " |"))
    for values in frame.itertuples(index=False, name=None):
        def cell(value: object) -> str:
            if pd.isna(value):
                return "NA"
            if isinstance(value, float):
                return f"{value:.6g}"
            return str(value).replace("|", "\\|").replace("\n", " ")
        lines.append("| " + " | ".join(cell(value) for value in values) + " |")
    (out / (name.lower().replace(" ", "_") + ".md")).write_text("\n".join(lines) + "\n", encoding="utf-8")


def plot_figures(out: Path, quality: pd.DataFrame, cost: pd.DataFrame) -> None:
    """Write a precision/recall chart per rule and an API cost/F1 chart."""
    for rule, group in quality.groupby("rule"):
        group = group.sort_values("model_key")
        fig, axis = plt.subplots(figsize=(11, 5))
        x = list(range(len(group)))
        axis.plot(x, group.precision, "o-", label="Precision")
        axis.plot(x, group.recall, "s-", label="Recall")
        axis.set_xticks(x, group.model_key, rotation=45, ha="right")
        axis.set_ylim(-0.04, 1.04)
        axis.set_ylabel("Rate")
        axis.set_title(f"Rule {rule}: precision and recall")
        axis.legend()
        fig.tight_layout()
        fig.savefig(out / f"rule_{rule}_precision_recall.png", dpi=140)
        plt.close(fig)
    joined = quality.merge(cost, on=["rule", "model_key"])
    fig, axis = plt.subplots(figsize=(10, 6))
    for rule, group in joined.groupby("rule"):
        axis.scatter(group.mean_cost_usd_per_run, group.f1, label=f"Rule {rule}")
    axis.set_xlabel("Mean API cost per run (USD)")
    axis.set_ylabel("F1")
    axis.set_ylim(-0.04, 1.04)
    axis.legend()
    fig.tight_layout()
    fig.savefig(out / "cost_vs_f1.png", dpi=140)
    plt.close(fig)


def analyze(scores: Path, out: Path, min_lower: float = 0.80) -> dict[str, pd.DataFrame]:
    """Produce all tables and figures from scored instance and run CSVs."""
    if not 0 <= min_lower <= 1:
        raise ValueError("--min-lower must be between 0 and 1")
    instances, runs = load_scores(scores)
    instances = order_model_keys(instances)
    runs = order_model_keys(runs)
    out.mkdir(parents=True, exist_ok=True)
    quality = metrics(instances)
    cost = cost_table(runs)
    tables = {"Precision recall F1": quality, "Rule 3 binaries": rule3_rates(instances),
              "Collateral per run": collateral_rates(runs), "Native planted recall": native_planted(instances),
              "Run flags": run_flags(runs), "Repeat stability": repeat_stability(instances),
              "Passage recall spread": passage_spread(instances), "Paired tiers": paired_tiers(instances),
              "API cost": cost, "Routing": routing(quality, cost, (0.70, 0.90, min_lower)),
              "Reasoning effect": reasoning_effect(instances, runs)}
    for name, frame in tables.items():
        note = "Claude cost is list-price-equivalent under subscription." if name == "API cost" else ""
        if name == "Reasoning effect":
            note = "All-rules is the headline row. Claude cost is list-price-equivalent under subscription."
        if name == "Repeat stability":
            note = "Only complete three-repeat instance cells count. Rule 3 framings are separate cells."
        if name == "Collateral per run":
            note = "Values are mean counts per run, not fractions of edits."
        write_table(out, name, frame, note)
    plot_figures(out, quality, cost)
    return tables


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scores", type=Path, default=Path("scores"))
    parser.add_argument("--out", type=Path, default=Path("analysis_out"))
    parser.add_argument("--min-lower", type=float, default=0.80)
    args = parser.parse_args()
    tables = analyze(args.scores, args.out, args.min_lower)
    print(f"Wrote {len(tables)} tables and {len(list(args.out.glob('*.png')))} figures to {args.out}")


if __name__ == "__main__":
    main()
