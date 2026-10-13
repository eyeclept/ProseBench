"""Generate deterministic synthetic scorer CSVs for analysis tests and demos."""

import argparse
import csv
import json
import logging
from pathlib import Path

from bench.score.score_runs import INSTANCE_FIELDS, RUN_FIELDS

logger = logging.getLogger(__name__)
BASE_MODELS = ("qwen36", "qwen38flash", "mistral_small4", "glm53flash", "mimo26pro",
               "mistral_large4", "haiku55", "sonnet55", "opus55")
MODELS = BASE_MODELS + ("qwen36_high", "qwen38flash_high")
COSTS = {"qwen36": 0.0001, "qwen38flash": 0.0001, "mistral_small4": 0.0004,
         "glm53flash": 0.0002, "mimo26pro": 0.001, "mistral_large4": 0.0015,
         "haiku55": 0.0012, "sonnet55": 0.003, "opus55": 0.006,
         "qwen36_high": 0.0003, "qwen38flash_high": 0.0003}


def generate(out: Path) -> tuple[int, int]:
    """Write nine min-reasoning models plus two high variants with known metrics."""
    out.mkdir(parents=True, exist_ok=True)
    instance_rows = []
    run_rows = []
    for model in MODELS:
        high = model.endswith("_high")
        base = model[:-5] if high else model
        for rule in range(1, 6):
            for passage_number in range(1, 4):
                for repeat in range(1, 4):
                    for framing in (("verbatim", "easy") if rule == 3 else ("verbatim",)):
                        passage = f"P{passage_number}"
                        run_id = f"R{rule}_{passage}_r{repeat}" + ("_easy" if framing == "easy" else "")
                        labels = {label: 0 for label in ("TP", "FN", "FP", "TN")}
                        binaries = {key: [] for key in ("ordinary_cut", "field_specific_promoted", "ambiguous_flagged")}
                        for index in range(9):
                            positive = index < 6
                            subtype = (("ordinary", "field_specific", "ambiguous")[index // 2]
                                       if rule == 3 and positive else "synthetic")
                            kind = "native" if index % 2 == 0 else "planted"
                            if high:
                                correct = True
                            elif base in ("glm53flash", "opus55"):
                                correct = True
                            elif base == "mistral_small4":
                                correct = positive
                            elif base == "mimo26pro":
                                correct = not positive or repeat != 2
                            elif base == "qwen38flash":
                                correct = not (positive and index == 0 and passage_number == 1)
                            elif base == "qwen36":
                                correct = not (positive and index == (repeat + passage_number) % 6)
                            elif base == "haiku55":
                                correct = not (positive and index in (0, 1))
                            else:
                                correct = not (positive and index == 1)
                            label = ("TP" if correct else "FN") if positive else ("TN" if correct else "FP")
                            labels[label] += 1
                            outcome = ("edited" if correct else "untouched") if positive else (
                                "untouched" if correct else "edited")
                            if rule == 3 and positive:
                                key = ("ordinary_cut", "field_specific_promoted", "ambiguous_flagged")[index // 2]
                                binaries[key].append(int(correct))
                                if index >= 4 and correct:
                                    outcome = "flagged"
                            row = dict(run_id=run_id, model_key=model,
                                       endpoint_model=model,
                                       rule=rule, passage=passage, repeat=repeat, framing=framing,
                                       instance_id=f"{passage}-R{rule}-{index + 1:03d}", kind=kind,
                                       polarity="flag" if rule == 3 and index in (4, 5) else (
                                           "change" if positive else "keep"), subtype=subtype,
                                       expected_action="flag" if rule == 3 and index in (4, 5) else (
                                           "cut" if positive else "keep"),
                                       outcome=outcome, label=label, flags="[]", judge_reason="")
                            for key in binaries:
                                row[key] = int(correct) if positive and key == (
                                    ("ordinary_cut", "field_specific_promoted", "ambiguous_flagged")[index // 2]) else ""
                            instance_rows.append(row)
                        fabricate = base == "mistral_small4" and rule in (1, 5) and repeat == 1
                        run_rows.append(dict(run_id=run_id, model_key=model,
                                             endpoint_model=model,
                                             rule=rule, passage=passage, repeat=repeat, framing=framing,
                                             thinking="high" if high else "none", cost_usd=COSTS[model],
                                             usage_input=600, usage_output=400 if high else 200, usage_cache_read=0,
                                             usage_cache_write=0,
                                             usage_reasoning=100 if high else (50 if base.startswith("mimo") else 0),
                                             duration_s=1.2, parse_error=False,
                                             invalid_edit_count=1 if base == "mistral_small4" and repeat == 1 else 0,
                                             n_tool_calls=1 if base == "mistral_small4" and repeat == 1 else 0,
                                             firecrawl_called=base == "mistral_small4" and repeat == 1,
                                             **labels, precision=(labels["TP"] / (labels["TP"] + labels["FP"])
                                                                  if labels["TP"] + labels["FP"] else ""),
                                             recall=labels["TP"] / (labels["TP"] + labels["FN"]),
                                             collateral_count=2 if base == "mistral_small4" else 0,
                                             other_rule_instance=1 if base == "mistral_small4" else 0,
                                             uncatalogued_text=1 if base == "mistral_small4" else 0,
                                             nonkeyboard_remaining="[]",
                                             fabricated_numbers=json.dumps(["98765"] if fabricate else []),
                                             **{key: int(all(values)) if rule == 3 else "" for key, values in binaries.items()}))
    for name, rows, fields in (("instances.csv", instance_rows, INSTANCE_FIELDS),
                               ("runs.csv", run_rows, RUN_FIELDS)):
        with (out / name).open("w", newline="", encoding="utf-8") as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    return len(instance_rows), len(run_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("synthetic_scores"))
    args = parser.parse_args()
    instances, runs = generate(args.out)
    print(f"Wrote {instances} instances and {runs} runs to {args.out}")


if __name__ == "__main__":
    main()
