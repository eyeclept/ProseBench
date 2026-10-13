"""Compare analytic DGX Spark output-token costs with plan-listed API rates."""

import argparse
import csv
import logging
from collections import defaultdict
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT = ROOT / "bench/analysis/hardware.yml"
DEFAULT_OUTPUT = ROOT / "bench/analysis/cost_comparison.csv"
FIELDS = ("axis", "model_key", "model", "total_params_b", "active_params_b",
          "ngram_embedding_params_b", "boxes", "quantization", "decode_tokens_s",
          "throughput_estimated", "duty_cycle", "hardware_usd_per_million_output",
          "api_usd_per_million_output", "usage_input", "usage_output",
          "usage_reasoning", "study_hardware_usd")


def number(item):
    """Get a sourced scalar, while accepting None for undisclosed values."""
    return None if item is None else item["value"]


def price_per_million(hardware, assumptions, boxes, tokens_s, productive_hours_day):
    """Charge straight-line capex to productive hours and power to decode time."""
    if boxes <= 0 or tokens_s <= 0 or productive_hours_day <= 0:
        raise ValueError("boxes, tokens_s, and productive_hours_day must be positive")
    capex = (boxes * number(hardware["unit_price_usd"]) /
             (number(assumptions["amortization_years"]) * number(assumptions["days_per_year"])
              * productive_hours_day))
    power = (boxes * number(hardware["load_power_w"]) / 1000
             * number(assumptions["electricity_usd_kwh"]))
    return ((capex + power) / (tokens_s * number(assumptions["seconds_per_hour"]))
            * number(assumptions["tokens_per_million"]))


def load_usage(path):
    """Read scorer runs and sum usage by model_key."""
    counts = defaultdict(lambda: {"usage_input": 0, "usage_output": 0, "usage_reasoning": 0})
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        required = {"model_key", "usage_input", "usage_output", "usage_reasoning"}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError(f"Missing runs CSV columns: {', '.join(sorted(required - set(reader.fieldnames or [])))}")
        for row in reader:
            key = row["model_key"]
            for field in ("usage_input", "usage_output", "usage_reasoning"):
                try:
                    value = int(row[field])
                except (ValueError, TypeError) as exc:
                    logger.exception("Invalid %s for %s", field, key)
                    raise ValueError(f"Invalid {field} for {key}: {row[field]!r}") from exc
                if value < 0:
                    raise ValueError(f"Negative {field} for {key}")
                counts[key][field] += value
    return counts


def comparison_rows(data, usage=None):
    """Emit one analytic hardware comparison per local model and duty cycle."""
    hardware, assumptions = data["hardware"], data["assumptions"]
    for key, model in data["models"].items():
        if model.get("deployment") == "cloud_only":
            continue
        boxes = number(model["boxes"])
        speed = number(model["decode_tokens_s"])
        keys = [key]
        high = f"{key}_high"
        if usage and high in usage:
            keys.append(high)
        for emit in keys:
            totals = (usage or {}).get(emit)
            for duty in assumptions["duty_cycles"]:
                cost = price_per_million(hardware, assumptions, boxes, speed,
                                         number(duty["hours_per_day"]))
                yield {"axis": "analytic", "model_key": emit, "model": model["name"],
                       "total_params_b": (">" if model["total_params_b"].get("qualifier") == "greater_than" else "")
                       + str(number(model["total_params_b"])),
                       "active_params_b": number(model["active_params_b"]),
                       "ngram_embedding_params_b": number(model.get("ngram_embedding_params_b")) or "",
                       "boxes": boxes, "quantization": model["quantization"]["name"],
                       "decode_tokens_s": speed,
                       "throughput_estimated": bool(model["decode_tokens_s"].get("estimated", False)),
                       "duty_cycle": duty["name"],
                       "hardware_usd_per_million_output": cost,
                       "api_usd_per_million_output": number(model["api_output_usd_per_million"]),
                       "usage_input": totals["usage_input"] if totals else "",
                       "usage_output": totals["usage_output"] if totals else "",
                       "usage_reasoning": totals["usage_reasoning"] if totals else "",
                       "study_hardware_usd": (cost * totals["usage_output"] / number(assumptions["tokens_per_million"]))
                       if totals else ""}



def markdown_table(rows):
    """Print distinct total, active, and box-count columns in an analytic table."""
    lines = ["Analytic hardware axis: output tokens only; single-stream published decode rates.",
             "| Model | Total B | Active B | N-gram B | Boxes | Quant | Decode tok/s | Duty | Hardware $/M output | API $/M output | Study output tokens | Study hardware $ |",
             "|---|---:|---:|---:|---:|---|---:|---|---:|---:|---:|---:|"]
    for row in rows:
        api = row["api_usd_per_million_output"]
        studied = row["study_hardware_usd"]
        lines.append("| " + " | ".join((row["model"], str(row["total_params_b"]),
                     str(row["active_params_b"]), str(row["ngram_embedding_params_b"] or "-"),
                     str(row["boxes"]), row["quantization"],
                     f"{row['decode_tokens_s']:g}" + (" (est.)" if row["throughput_estimated"] else ""),
                     row["duty_cycle"], f"{row['hardware_usd_per_million_output']:.4f}",
                     f"{api:.4f}" if api is not None else "n/a (self-hosted)",
                     str(row["usage_output"]) if row["usage_output"] != "" else "-",
                     f"{studied:.6f}" if studied != "" else "-")) + " |")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hardware-yml", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--csv-output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--runs-csv", type=Path, help="Optional scorer scores/runs.csv")
    args = parser.parse_args(argv)
    data = yaml.safe_load(args.hardware_yml.read_text(encoding="utf-8"))
    usage = load_usage(args.runs_csv) if args.runs_csv else None
    rows = list(comparison_rows(data, usage))
    args.csv_output.parent.mkdir(parents=True, exist_ok=True)
    with args.csv_output.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(markdown_table(rows))
    print(f"CSV: {args.csv_output}")


if __name__ == "__main__":
    main()
