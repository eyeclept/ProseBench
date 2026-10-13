"""Test sourced hardware cost arithmetic and scorer-run usage aggregation."""

import csv
import logging
from pathlib import Path

import pytest
import yaml

from bench.analysis import cost_model

logger = logging.getLogger(__name__)


def test_hand_computed_hourly_cost():
    hardware = {"unit_price_usd": {"value": 1000}, "load_power_w": {"value": 200}}
    assumptions = {"amortization_years": {"value": 2},
                   "days_per_year": {"value": 100},
                   "electricity_usd_kwh": {"value": 0.2},
                   "seconds_per_hour": {"value": 3600},
                   "tokens_per_million": {"value": 1000000}}
    # Two boxes cost $2,000 / 2,000 productive hours = $1/h.
    # 400 W at $0.20/kWh costs $0.08/h. At 50 tok/s, 180,000 tok/h costs $1.08.
    assert cost_model.price_per_million(hardware, assumptions, 2, 50, 10) == pytest.approx(6)
    assert cost_model.price_per_million(hardware, assumptions, 2, 50, 20) == pytest.approx(3.2222222222)


def test_cli_runs_csv_groups_real_endpoint_usage(tmp_path, capsys):
    runs = tmp_path / "runs.csv"
    with runs.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=("run_id", "model_key", "endpoint_model",
                                                  "usage_input", "usage_output", "usage_reasoning"))
        writer.writeheader()
        writer.writerows([
            {"run_id": "a", "model_key": "qwen36", "endpoint_model": "openrouter/qwen36",
             "usage_input": 100, "usage_output": 40, "usage_reasoning": 10},
            {"run_id": "b", "model_key": "qwen36", "endpoint_model": "openrouter/qwen36",
             "usage_input": 150, "usage_output": 60, "usage_reasoning": 5},
            {"run_id": "c", "model_key": "qwen36_high", "endpoint_model": "openrouter/qwen36",
             "usage_input": 200, "usage_output": 80, "usage_reasoning": 15},
        ])
    dest = tmp_path / "comparison.csv"
    cost_model.main(["--runs-csv", str(runs), "--csv-output", str(dest)])
    output = capsys.readouterr().out
    with dest.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    assert len(rows) == 10
    assert set(row["axis"] for row in rows) == {"analytic"}
    assert {row["model_key"] for row in rows} == {"qwen36", "qwen36_high", "qwen38flash",
                                                   "mistral_small4", "glm53flash"}
    qwen = next(row for row in rows if row["model_key"] == "qwen36" and row["duty_cycle"] == "8h/day")
    high = next(row for row in rows if row["model_key"] == "qwen36_high" and row["duty_cycle"] == "8h/day")
    assert (qwen["usage_input"], qwen["usage_output"], qwen["usage_reasoning"]) == ("250", "100", "15")
    assert (high["usage_input"], high["usage_output"], high["usage_reasoning"]) == ("200", "80", "15")
    assert qwen["hardware_usd_per_million_output"] == high["hardware_usd_per_million_output"]
    assert float(high["study_hardware_usd"]) == pytest.approx(float(high["hardware_usd_per_million_output"]) * 80 / 1000000)
    assert next(row for row in rows if row["model_key"] == "mistral_small4")["usage_output"] == ""
    assert "Analytic hardware axis" in output
    assert "GLM-5.3-Flash" in output



def test_every_numeric_input_traces_to_source_or_formula():
    data = yaml.safe_load(cost_model.DEFAULT_INPUT.read_text(encoding="utf-8"))

    def inspect(item):
        if isinstance(item, dict):
            if "value" in item:
                assert isinstance(item["value"], (int, float))
                assert item.get("source_url") or (item.get("estimated") is True and item.get("formula"))
                assert item.get("accessed") == "2026-10-12"
            for value in item.values():
                inspect(value)
        elif isinstance(item, list):
            for value in item:
                inspect(value)

    inspect(data)
