"""Test prompt assembly, event extraction, and guarded wrapper execution."""

from __future__ import annotations

import hashlib
import json
import logging
import os
import shutil
import tempfile
from pathlib import Path

import pytest
import yaml

from bench.runner import run_matrix
from bench.runner.omp_events import parse_edits, parse_events
from bench.runner.prompt import assemble

logger = logging.getLogger(__name__)

# The event keys and usage shape come from ProseCleanup proseTestSuite/outputs/claude-opus-5/q1.jsonl.
FAKE_WRAPPER = '''#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
args = sys.argv
model = args[args.index("--model") + 1]
level = args[args.index("--thinking") + 1]
prompt = Path(args[args.index("--prompt-file") + 1]).read_text()
with open(os.environ["FAKE_TRACE"], "a") as trace:
    trace.write(json.dumps({"model": model, "thinking": level, "prompt": prompt}) + "\\n")
mode = os.environ.get("FAKE_MODE", "success")
if mode == "retry" and model.endswith("ornith"):
    print(json.dumps({"type": "error", "message": "endpoint unavailable"}))
    sys.exit(1)
if mode == "empty" and model.endswith("ornith"):
    print(json.dumps({"type": "agent_end", "messages": []}))
    sys.exit(0)
text = os.environ.get("FAKE_TEXT", '{"edits": [{"original": "word", "replacement": "", "reason": "cut"}]}')
print(json.dumps({"type": "tool_execution_start", "toolName": "web_search", "args": {"query": "query"}}))
print(json.dumps({"type": "agent_end", "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}]}, {"role": "assistant", "content": [{"type": "thinking", "thinking": "reasoning"}, {"type": "text", "text": text}], "usage": {"input": 12, "output": 23, "cacheRead": 4, "cacheWrite": 5, "reasoningTokens": 7, "cost": {"total": 0.003}}}]}))
'''


@pytest.fixture
def sandbox(monkeypatch):
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent, prefix=".sandbox-") as directory:
        root = Path(directory)
        for folder in ("prompts", "rules"):
            shutil.copytree(run_matrix.ROOT / "bench" / folder, root / "bench" / folder)
        for name in ("P1", "P2", "P3"):
            passage_dir = root / "bench" / "corpus" / "out" / name
            passage_dir.mkdir(parents=True)
            (passage_dir / "injected.md").write_text("A word and a claim.\n", encoding="utf-8")
        roster = {"scored": {"ornith": {"model": "fake/ornith", "thinking": "low"}, "qwen38flash": {"model": "fake/qwen38", "thinking": "none"}}, "fallback": {"qwen36": {"model": "fake/qwen36", "thinking": "low"}}, "routing": {"t1_projection_limit_tokens": 60000, "harness_overhead_tokens": 0}}
        (root / "bench" / "roster.yml").write_text(yaml.safe_dump(roster), encoding="utf-8")
        (root / "bench" / "runner").mkdir()
        (root / "container").mkdir()
        (root / "container" / "pin.env").write_text("PROSEBENCH_OMP_VERSION=18.10.3\nPROSEBENCH_IMAGE_DIGEST=sha256:abc\n", encoding="utf-8")
        wrapper = root / "bench" / "runner" / "fake-omp-run"
        wrapper.write_text(FAKE_WRAPPER, encoding="utf-8")
        wrapper.chmod(0o755)
        monkeypatch.setenv("PROSEBENCH_OMP_RUN", str(wrapper))
        monkeypatch.setenv("FAKE_TRACE", str(root / "trace.jsonl"))
        monkeypatch.setattr(run_matrix, "ROOT", root)
        yield root, roster, wrapper


def trace(root):
    path = root / "trace.jsonl"
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def test_prompt_fill_and_hashes(sandbox):
    root, _, _ = sandbox
    first = assemble(root, 1, "P1")
    reference = (root / "bench" / "rules" / "banned-words-phrases.md").read_text()
    assert '\n<reference name="banned-words-phrases.md">\n' + reference + '\n</reference>\n' in first.user
    assert "{rule_text}" not in first.user
    assert first.prompt_sha256 == hashlib.sha256(first.user.encode()).hexdigest()
    assert first.system_prompt_sha256 == hashlib.sha256(first.system.encode()).hexdigest()
    assert first.rule_text_sha256 == hashlib.sha256(first.rule_text.encode()).hexdigest()
    assert first.passage_sha256 == hashlib.sha256(first.passage.encode()).hexdigest()
    easy = assemble(root, 3, "P1", "easy")
    assert "<escalation>" in easy.user
    assert "<escalation>" not in assemble(root, 3, "P1").user
    assert "<reference name=" not in easy.user
    assert "<escalation>" not in assemble(root, 2, "P1").user


@pytest.mark.parametrize("text,expected", [
    ('```json\n{"edits": []}\n```', []),
    ('Here are edits:\n{"edits":[{"original":"word","replacement":null,"reason":"unclear"}]}\nDone.', [{"original": "word", "replacement": None, "reason": "unclear"}]),
    ('{"edits": [oops]}', None),
    ('not JSON', None),
])
def test_edit_parsing(text, expected):
    edits, error = parse_edits(text)
    assert edits == expected
    assert (error is None) == (expected is not None)


def test_real_shape_events():
    raw = '\n'.join((json.dumps({"type": "tool_execution_start", "toolName": "web_search", "args": {"query": "fact"}}), json.dumps({"type": "agent_end", "messages": [{"role": "assistant", "content": [{"type": "thinking", "thinking": "hidden"}, {"type": "text", "text": '{"edits": []}'}], "usage": {"input": 1, "output": 2, "cacheRead": 3, "cacheWrite": 4, "reasoningTokens": 5, "cost": {"total": 0.006}}}]})))
    result = parse_events(raw)
    assert result.output_text == '{"edits": []}'
    assert result.usage == {"input": 1, "output": 2, "cache_read": 3, "cache_write": 4, "reasoning": 5}
    assert result.cost_usd == 0.006
    assert result.tool_calls == [{"name": "web_search", "arguments": {"query": "fact"}}]


def test_multiple_assistant_turns_are_charged():
    messages = [
        {"role": "assistant", "content": [{"type": "toolCall", "name": "web_search"}], "usage": {"input": 10, "output": 20, "reasoningTokens": 2, "cost": {"total": 0.002}}},
        {"role": "assistant", "content": [{"type": "text", "text": '{"edits": []}'}], "usage": {"input": 30, "output": 40, "reasoningTokens": 3, "cost": {"total": 0.004}}},
    ]
    event = parse_events(json.dumps({"type": "agent_end", "messages": messages}))
    assert event.output_text == '{"edits": []}'
    assert event.usage["input"] == 40 and event.usage["reasoning"] == 5
    assert event.cost_usd == 0.006


def test_record_resume_force_and_atomic(sandbox, monkeypatch):
    root, roster, wrapper = sandbox
    result = run_matrix.execute(root, "qwen38flash", 1, "P1", 1, "verbatim", roster, str(wrapper))
    path = root / "runs" / "qwen38flash" / "R1_P1_r1.json"
    assert json.loads(path.read_text()) == result
    assert (path.with_suffix(".jsonl")).read_text().splitlines()[0].startswith('{"type": "tool_execution_start"')
    assert result["model_key"] == "qwen38flash" and result["endpoint_model"] == "fake/qwen38"
    assert result["thinking"] == "none" and result["exit_code"] == 0 and result["error"] is None
    assert result["edits"] == [{"original": "word", "replacement": "", "reason": "cut"}]
    assert result["usage"] == {"input": 12, "output": 23, "cache_read": 4, "cache_write": 5, "reasoning": 7}
    assert result["cost_usd"] == 0.003 and result["tool_calls"][0]["name"] == "web_search"
    assert result["omp_version"] == "18.10.3" and result["image_digest"] == "sha256:abc"
    assert result["started_at"] and result["duration_s"] >= 0
    assert run_matrix.execute(root, "qwen38flash", 1, "P1", 1, "verbatim", roster, str(wrapper)) is None
    assert len(trace(root)) == 1
    assert run_matrix.execute(root, "qwen38flash", 1, "P1", 1, "verbatim", roster, str(wrapper), force=True)
    assert len(trace(root)) == 2
    prior_record = path.read_bytes()
    original = Path.replace
    def broken_replace(self, target):
        if str(target).endswith("R1_P1_r1.json"):
            raise OSError("injected atomic failure")
        return original(self, target)
    monkeypatch.setattr(Path, "replace", broken_replace)
    with pytest.raises(OSError, match="injected atomic failure"):
        run_matrix.execute(root, "qwen38flash", 1, "P1", 1, "verbatim", roster, str(wrapper), force=True)
    assert path.read_bytes() == prior_record
    assert not list(path.parent.glob(".R1_P1_r1.json.*"))


def test_routing_and_retries(sandbox, monkeypatch):
    root, roster, wrapper = sandbox
    roster["routing"]["t1_projection_limit_tokens"] = 4000
    projected = run_matrix.execute(root, "ornith", 1, "P1", 1, "verbatim", roster, str(wrapper))
    assert projected["routed"] and projected["route_reason"] == "projected_over_60000"
    assert projected["model_key"] == "ornith" and projected["endpoint_model"] == "fake/qwen36"
    assert [entry["model"] for entry in trace(root)] == ["fake/qwen36"]
    roster["routing"]["t1_projection_limit_tokens"] = 60000
    monkeypatch.setenv("FAKE_MODE", "retry")
    retried = run_matrix.execute(root, "ornith", 2, "P1", 1, "verbatim", roster, str(wrapper))
    assert retried["route_reason"] == "t1_failure" and retried["error"] is None
    assert [entry["model"] for entry in trace(root)][1:] == ["fake/ornith", "fake/ornith", "fake/qwen36"]
    assert retried["cost_usd"] == 0.003
    monkeypatch.setenv("FAKE_MODE", "empty")
    empty = run_matrix.execute(root, "ornith", 3, "P1", 1, "verbatim", roster, str(wrapper))
    assert empty["route_reason"] == "t1_failure"
    column = run_matrix.execute(root, "ornith", 4, "P1", 1, "verbatim", roster, str(wrapper), column_fallback=True)
    assert column["route_reason"] == "t1_column_fallback"
    assert [entry["model"] for entry in trace(root)][-1] == "fake/qwen36"


def test_unverified_refusal_and_plan_guard(sandbox, monkeypatch, capsys):
    root, roster, wrapper = sandbox
    roster["scored"]["qwen38flash"]["thinking"] = "unverified"
    (root / "bench" / "roster.yml").write_text(yaml.safe_dump(roster))
    assert run_matrix.main(["--models", "qwen38flash", "--pilot", "--yes"]) == 2
    assert not trace(root)
    assert run_matrix.main(["--models", "ornith", "--pilot"]) == 2
    assert not trace(root)
    assert "Planned runs: 6" in capsys.readouterr().out
    assert run_matrix.main(["--models", "ornith", "--pilot", "--dry-run"]) == 0
    output = capsys.readouterr().out
    assert "Planned runs: 6" in output and output.count("projected_tokens=") == 6
    assert not trace(root)


def test_unparseable_record(sandbox, monkeypatch):
    root, roster, wrapper = sandbox
    monkeypatch.setenv("FAKE_TEXT", "not JSON")
    record = run_matrix.execute(root, "qwen38flash", 5, "P1", 1, "verbatim", roster, str(wrapper))
    assert record["edits"] is None and record["parse_error"] == "no JSON object in final assistant text"


def test_nine_column_dry_run_counts(sandbox, capsys):
    root, _, _ = sandbox
    shutil.copyfile(Path(__file__).resolve().parents[2] / "roster.yml", root / "bench" / "roster.yml")
    assert run_matrix.main(["--dry-run", "--pilot", "--models", "all"]) == 0
    output = capsys.readouterr().out
    assert "Planned runs: 54" in output and output.count("projected_tokens=") == 54
    assert run_matrix.main(["--dry-run", "--models", "all"]) == 0
    output = capsys.readouterr().out
    assert "Planned runs: 486" in output and output.count("projected_tokens=") == 486
    assert not trace(root)


def test_cli_uses_wrapper_and_resumes(sandbox, capsys):
    root, _, _ = sandbox
    argv = ["--models", "ornith", "--rules", "1", "--passages", "P1", "--repeats", "1", "--framings", "verbatim", "--yes"]
    assert run_matrix.main(argv) == 0
    assert "Planned runs: 1" in capsys.readouterr().out
    assert len(trace(root)) == 1
    assert (root / "runs" / "ornith" / "R1_P1_r1.json").is_file()
    assert run_matrix.main(argv) == 0
    assert len(trace(root)) == 1
    assert run_matrix.main(argv + ["--force"]) == 0
    assert len(trace(root)) == 2
