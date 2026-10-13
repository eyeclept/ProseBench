"""Check that analysis recovers planted synthetic score structure."""

import csv
import logging
import subprocess
import sys

import pytest

from bench.analysis.analyze import analyze
from bench.analysis.fixtures import generate
from bench.analysis.kappa import agreement
from bench.score.diff_report import FIELDS

logger = logging.getLogger(__name__)


def test_analysis_recovers_structure(tmp_path):
    scores = tmp_path / "scores"
    n_instances, n_runs = generate(scores)
    assert n_runs == 9 * 54
    assert n_instances == 9 * 54 * 9
    out = tmp_path / "analysis"
    tables = analyze(scores, out)
    quality = tables["Precision recall F1"]
    perfect = quality[(quality.rule == 1) & (quality.model_key == "glm53flash")].iloc[0]
    assert perfect.precision == perfect.recall == perfect.f1 == 1
    assert 0.9 < perfect.precision_low < 1
    assert 0.9 < perfect.recall_low < 1
    overapply = quality[(quality.rule == 1) & (quality.model_key == "mistral_small4")].iloc[0]
    assert overapply.FP == 27
    assert overapply.precision < 0.7
    stability = tables["Repeat stability"]
    unstable = stability[(stability.rule == 1) & (stability.model_key == "mimo26pro")].iloc[0]
    assert unstable.stable_fraction < 0.5
    assert tables["Routed Ornith"].query("rule == 1").iloc[0].TP == 5
    assert tables["API cost"].query("rule == 1 and model_key == 'ornith'").iloc[0].runs == 8
    assert tables["Routed Ornith cost"].query("rule == 1").iloc[0].runs == 1
    assert tables["Run flags"].set_index("model_key").loc["mistral_small4", "fabricated_number_rate"] > 0
    assert tables["Collateral per run"].query("rule == 1 and model_key == 'mistral_small4'").iloc[0].collateral_count == 2
    route = tables["Routing"].query("rule == 1").set_index("threshold")
    assert route.loc[0.7, "model_key"] == "ornith"
    assert route.loc[0.8, "model_key"] == "qwen38flash"
    assert route.loc[0.9, "model_key"] == "glm53flash"
    assert len(tables["Rule 3 binaries"]) == 9 * 2 * 3
    assert len(tables["Paired tiers"].query("rule == 1")) == 8
    assert (out / "rule_1_precision_recall.png").is_file()
    assert (out / "rule_5_precision_recall.png").is_file()
    assert (out / "cost_vs_f1.png").is_file()
    assert (out / "routing.md").is_file()
    assert "list-price-equivalent under subscription" in (out / "api_cost.md").read_text()


def test_routed_merge_and_custom_threshold(tmp_path):
    scores = tmp_path / "scores"
    generate(scores)
    tables = analyze(scores, tmp_path / "merged", min_lower=0.95, include_routed=True)
    assert tables["API cost"].query("rule == 1 and model_key == 'ornith'").iloc[0].runs == 9
    route = tables["Routing"].query("rule == 1").set_index("threshold")
    assert route.loc[0.95, "model_key"] == "None qualifies"
    assert tables["Routed Ornith"].query("rule == 1").iloc[0].TP == 5


def test_kappa_hand_calculated(tmp_path):
    scores = tmp_path / "scores"
    generate(scores)
    worksheet = tmp_path / "worksheet.csv"
    rows = []
    with (scores / "instances.csv").open(newline="", encoding="utf-8") as stream:
        for row in csv.DictReader(stream):
            if row["model_key"] == "glm53flash" and row["rule"] == "1" and row["repeat"] == "1":
                if row["instance_id"] in ("P1-R1-001", "P1-R1-002", "P1-R1-007", "P1-R1-008"):
                    rows.append(row)
    rows.sort(key=lambda row: row["instance_id"])
    assert len(rows) == 4
    # Owner TP, TP, TN, TP versus scorer TP, TP, TN, TN gives kappa 0.5.
    with worksheet.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=FIELDS)
        writer.writeheader()
        for row, owner in zip(rows, ("TP", "TP", "TN", "TP")):
            writer.writerow({**{field: row.get(field, "") for field in FIELDS}, "owner_label": owner})
    result = agreement(worksheet, scores / "instances.csv")
    assert result.loc[result.rule == "overall", "kappa"].iloc[0] == pytest.approx(0.5)
    assert result.loc[result.rule == "1", "result"].iloc[0] == "FAIL"
    assert result.loc[result.rule == "1", "ci_low"].iloc[0] <= 0.5


def test_command_line_generates_figures(tmp_path):
    scores = tmp_path / "scores"
    out = tmp_path / "figures"
    generated = subprocess.run([sys.executable, "-m", "bench.analysis.fixtures",
                                "--out", str(scores)], capture_output=True, text=True, check=True)
    assert "486 runs" in generated.stdout
    result = subprocess.run([sys.executable, "-m", "bench.analysis.analyze",
                             "--scores", str(scores), "--out", str(out)],
                            capture_output=True, text=True, check=True)
    assert "6 figures" in result.stdout
    assert len(list(out.glob("rule_*_precision_recall.png"))) == 5
