"""Exercise the scorer on compact answer keys and synthetic run records."""

import csv
import json
import logging
import sys
from types import SimpleNamespace

import pytest

from bench.score.apply_edits import apply_edits
from bench.score.diff_report import sample_records, write_report
from bench.score.score_runs import score_one, score_runs

logger = logging.getLogger(__name__)


@pytest.fixture
def fixture_data():
    specs = [
        (1, "fact_available", "change", "replace_with_fact", "significantly improved", "12 percent"),
        (1, "no_fact", "change", "cut", "foster innovation", None),
        (1, "technical_term", "keep", "keep", "statistically significant", None),
        (2, "windup", "change", "cut", "It is important to note that ", None),
        (2, "loadbearing", "keep", "keep", "not available", None),
        (2, "doubling", "change", "cut", "and tidy", None),
        (3, "ordinary", "change", "cut", "rather than by accident", None),
        (3, "field_specific", "change", "promote_to_sentence", "not a built system", None),
        (3, "ambiguous", "flag", "flag", "rather than modeled", None),
        (4, "emdash_clauses", "change", "punct_semicolon_or_period", "\u2014", None),
        (4, "emdash_fragment", "change", "punct_comma", "\u2014an early prototype\u2014", None),
        (4, "emdash_runon", "change", "punct_split", "\u2014The", None),
        (4, "endash_range", "change", "punct_hyphen", "\u2013", None),
        (4, "curly_quote", "change", "punct_straight_quote", "\u201carchive\u201d", None),
        (4, "ellipsis", "change", "punct_three_periods", "\u2026", None),
        (4, "diacritic", "keep", "keep", "caf\u00e9", None),
        (4, "other_nonkeyboard", "change", "ascii_equivalent", "\u2022", None),
        (5, "number_available", "change", "replace_with_fact", "very rapidly", "12 seconds"),
        (5, "no_number", "change", "cut", "very bright", None),
        (5, "finality_exclusive", "change", "cut", "only ", None),
        (5, "emphatic_no_exclusive", "keep", "keep", "not only", None),
    ]
    lines = [
        "The system significantly improved; it saved 12 percent.",
        "Leaders foster innovation.",
        "The result was statistically significant.",
        "It is important to note that the tool worked.",
        "The feed was not available.",
        "The room was clean and tidy.",
        "The fault occurred on purpose, rather than by accident.",
        "This is a vision paper, not a built system.",
        "The plan is empirical, rather than modeled.",
        "The device shipped\u2014it failed.",
        "The device\u2014an early prototype\u2014worked.",
        "The alarms rang\u2014The servers stopped.",
        "Data span 1990\u20132000.",
        "They wrote \u201carchive\u201d today.",
        "Wait\u2026 then try again.",
        "She works at the caf\u00e9.",
        "List the \u2022 marker.",
        "The task finished very rapidly in 12 seconds.",
        "The lamp was very bright.",
        "The tool only works today.",
        "The plan was not only sound.",
        "Plain text stays here.",
    ]
    passage = "\n".join(lines)
    rows = []
    for index, ((rule, subtype, polarity, action, target, fact), line) in enumerate(zip(specs, lines, strict=False), 1):
        start = passage.index(line) + line.index(target)
        rows.append({"instance_id": f"P1-R{rule}-{index:03d}", "passage": "P1", "rule": rule,
                     "kind": "planted" if index % 2 else "native", "polarity": polarity,
                     "subtype": subtype, "expected_action": action,
                     "target_text": target, "char_start": start, "char_end": start + len(target),
                     "context_sentence": line, "fact_text": fact, "notes": ""})
    return passage, rows


def run(rule, edits, *, repeat=1):
    return {"run_id": f"R{rule}_P1_r{repeat}", "model_key": "fixture", "endpoint_model": "fixture-model",
            "rule": rule, "passage": "P1", "repeat": repeat, "framing": "verbatim",
            "routed": False, "route_reason": "", "thinking": "none", "cost_usd": 0.0,
            "usage": {"input": 2, "output": 3, "cache_read": 0, "cache_write": 0, "reasoning": 0},
            "duration_s": 0.1, "tool_calls": [], "parse_error": None,
            "edits": [{"original": before, "replacement": after, "reason": "fixture"}
                      for before, after in edits]}


def labels(scored):
    return {item["subtype"]: item["label"] for item in scored}


def mock_grok(monkeypatch, verdict="correct"):
    calls = []

    def answer(messages, **kwargs):
        request = json.loads(messages[1]["content"])
        calls.append(request)
        return {"content": json.dumps({"verdicts": [
            {"instance_id": item["instance_id"], "verdict": verdict, "reason": "fixture decision"}
            for item in request["items"]]})}

    monkeypatch.setitem(sys.modules, "bench.llm_clients", SimpleNamespace(grok_chat=answer))
    return calls


def test_apply_invalid_ambiguous_flag_and_provenance():
    applied = apply_edits("foo foo 42", [{"original": "foo", "replacement": "bar"},
                                          {"original": "absent", "replacement": "x"},
                                          {"original": "foo", "replacement": None}])
    assert applied.text == "bar foo 42"
    assert [item.status for item in applied.edit_spans] == ["ambiguous_applied", "invalid", "flag"]
    assert (applied.edit_spans[0].original_start, applied.edit_spans[0].original_end) == (0, 3)
    assert applied.region(0, 3) == "bar"


def test_rule1_rule2_expected_actions_and_touched_keep(fixture_data, tmp_path, monkeypatch):
    passage, key = fixture_data
    calls = mock_grok(monkeypatch)
    r1, _ = score_one(run(1, [("significantly improved", "improved by 12 percent"),
                              ("foster innovation", "")]), key, passage, tmp_path)
    assert labels(r1) == {"fact_available": "TP", "no_fact": "TP", "technical_term": "TN"}
    r2, _ = score_one(run(2, [("It is important to note that ", ""),
                              ("and tidy", "")]), key, passage, tmp_path)
    assert labels(r2) == {"windup": "TP", "loadbearing": "TN", "doubling": "TP"}
    protected, _ = score_one(run(1, [("statistically significant",
                                      "statistically significant")], repeat=4), key, passage, tmp_path)
    assert labels(protected)["technical_term"] == "TN"
    assert len(calls) == 2
    assert calls[1]["items"][0]["subtype"] == "technical_term"
    flagged, _ = score_one(run(1, [("statistically significant", None)], repeat=5),
                           key, passage, tmp_path)
    assert labels(flagged)["technical_term"] == "FP"


def test_rule4_subtypes_splice_and_overapplication(fixture_data, tmp_path):
    passage, key = fixture_data
    edits = [("\u2014", ";"), ("\u2014an early prototype\u2014", ", an early prototype,"),
             ("\u2014The", ". The"), ("\u2013", "-"),
             ("\u201carchive\u201d", '"archive"'), ("\u2026", "..."), ("\u2022", "-")]
    scored, summary = score_one(run(4, edits), key, passage, tmp_path)
    assert set(labels(scored).values()) == {"TP", "TN"}
    assert summary["nonkeyboard_remaining"] == "[]"
    wrong, _ = score_one(run(4, [("\u2014", ",")]), key, passage, tmp_path)
    assert labels(wrong)["emdash_clauses"] == "FN"
    assert "comma_splice_introduced" in json.loads(next(item["flags"] for item in wrong if item["subtype"] == "emdash_clauses"))
    over, _ = score_one(run(4, [("caf\u00e9", "cafe")], repeat=2), key, passage, tmp_path)
    assert labels(over)["diacritic"] == "FP"


def test_rule1_fabrication_invalid_and_collateral(fixture_data, tmp_path, monkeypatch):
    passage, key = fixture_data
    mock_grok(monkeypatch)
    edits = [("significantly improved", "improved 900 percent"),
             ("statistically significant", "irrelevant"), ("Plain text", "Other words"),
             ("missing phrase", ""), ("foster innovation", "")]
    scored, summary = score_one(run(1, edits), key, passage, tmp_path)
    assert labels(scored) == {"fact_available": "FN", "no_fact": "TP", "technical_term": "FP"}
    assert "fabricated_number" in json.loads(scored[0]["flags"])
    assert summary["invalid_edit_count"] == 1
    assert summary["uncatalogued_text"] == 1
    assert summary["other_rule_instance"] == 0
    _, other = score_one(run(2, [("foster innovation", ""), ("Plain text", "Elsewhere")]), key, passage, tmp_path)
    assert (other["other_rule_instance"], other["uncatalogued_text"]) == (1, 1)


def test_judge_both_ways_flag_and_rule3_binaries(fixture_data, tmp_path, monkeypatch):
    passage, key = fixture_data
    calls = mock_grok(monkeypatch, verdict="correct")
    edits = [("rather than by accident", ""),
             ("not a built system", "the authors describe a proposal. No implementation exists"),
             ("rather than modeled", None)]
    scored, summary = score_one(run(3, edits), key, passage, tmp_path)
    assert labels(scored) == {"ordinary": "TP", "field_specific": "TP", "ambiguous": "TP"}
    assert len(calls) == 1 and len(calls[0]["items"]) == 1
    assert (summary["ordinary_cut"], summary["field_specific_promoted"], summary["ambiguous_flagged"]) == (1, 1, 1)
    score_one(run(3, edits), key, passage, tmp_path)
    assert len(calls) == 1
    bad_calls = mock_grok(monkeypatch, verdict="incorrect")
    bad, _ = score_one(run(3, edits, repeat=2), key, passage, tmp_path)
    assert labels(bad)["field_specific"] == "FN" and len(bad_calls) == 1
    other_model = run(3, edits)
    other_model["model_key"] = "other-fixture"
    separate, _ = score_one(other_model, key, passage, tmp_path)
    assert labels(separate)["field_specific"] == "FN" and len(bad_calls) == 2
    keep, _ = score_one(run(2, [("not available", "unavailable")], repeat=3), key, passage, tmp_path)
    assert labels(keep)["loadbearing"] == "FP"
    assert len(bad_calls) == 3


def test_replacement_numbers_cut_rewrites_and_parse_failure(fixture_data, tmp_path, monkeypatch):
    passage, key = fixture_data
    calls = mock_grok(monkeypatch)
    scored, _ = score_one(run(5, [("very rapidly", "in 12 seconds"),
                                  ("very bright", "bright"), ("only ", "")]), key, passage, tmp_path)
    assert labels(scored) == {"number_available": "TP", "no_number": "TP",
                              "finality_exclusive": "TP", "emphatic_no_exclusive": "TN"}
    assert len(calls[0]["items"]) == 2
    bad, _ = score_one(run(5, [("very rapidly", "in 900 seconds")], repeat=2), key, passage, tmp_path)
    assert labels(bad)["number_available"] == "FN"
    assert "fabricated_number" in json.loads(bad[0]["flags"])
    missing = run(3, [])
    missing["parse_error"] = "invalid JSON"
    missing["edits"] = None
    rows, summary = score_one(missing, key, passage, tmp_path)
    assert all(item["label"] == "FN" for item in rows)
    assert summary["parse_error"] is True


def test_score_runs_csv_and_hand_worksheet(fixture_data, tmp_path, monkeypatch):
    passage, key = fixture_data
    calls = mock_grok(monkeypatch)
    corpus = tmp_path / "corpus"
    (corpus / "P1").mkdir(parents=True)
    (corpus / "P1" / "injected.md").write_text(passage, encoding="utf-8")
    answer = corpus / "answer_key.jsonl"
    answer.write_text("".join(json.dumps(row) + "\n" for row in key), encoding="utf-8")
    runs_dir = tmp_path / "runs" / "fixture"
    runs_dir.mkdir(parents=True)
    for record in (run(3, [("rather than by accident", ""),
                           ("not a built system", "This proposal has no built system"),
                           ("rather than modeled", None)]),
                   run(4, [("\u2014", ";"), ("\u2014an early prototype\u2014", ", an early prototype,")])):
        (runs_dir / (record["run_id"] + ".json")).write_text(json.dumps(record), encoding="utf-8")
    scores = tmp_path / "scores"
    instances, summary = score_runs(tmp_path / "runs", answer, corpus, scores)
    assert len(instances) == 11 and len(summary) == 2
    with (scores / "instances.csv").open(encoding="utf-8", newline="") as stream:
        assert len(list(csv.DictReader(stream))) == 11
    with (scores / "runs.csv").open(encoding="utf-8", newline="") as stream:
        saved = list(csv.DictReader(stream))
    assert saved[0]["usage_input"] == "2" and saved[0]["n_tool_calls"] == "0"
    assert len(calls) == 1
    sampled = write_report(tmp_path / "runs", answer, corpus, scores / "review.md", scores / "review.csv")
    assert len(sampled) == 3 and all(row["owner_label"] == "" for row in sampled)
    assert all(row["diff"].startswith("--- before\n+++ after\n") for row in sampled if row["before"] != row["after"])
    assert sample_records([(run(3, []), row) for row in key if row["rule"] == 3], 645) == sample_records(
        [(run(3, []), row) for row in key if row["rule"] == 3], 645)
    assert (scores / "review.md").exists() and (scores / "review.csv").exists()
