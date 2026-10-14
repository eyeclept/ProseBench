"""Rate scored instances with a blind AI rater: GPT-6.1 Sol, Grok 4.6, or TypeSafe Jev 1.13.

GPT runs on the owner's ChatGPT subscription, Grok on the owner's xAI OAuth, Jev on the OpenRouter Decisions
API. All three get the same rubric (rater_prompt.md) and the same items: rule text, answer-key entry, and the
before/after span. They are blind to the scorer's labels, the Grok judge's reasons, and each other. GPT and Grok
rate a batch per (model, run) call at the same reasoning effort; Jev has no text output, so it answers one
yes/no question per item and its verdict is P(correct) >= 0.5. Results are cached per rater and batch.
bench.analysis.rater_agreement compares the raters with each other and with the scorer. That is AI-AI
agreement, not human validation.
"""

import argparse
import csv
import hashlib
import json
import logging
from concurrent.futures import CancelledError, ThreadPoolExecutor, as_completed
from pathlib import Path

from bench.llm_clients import LlmError, LlmQuotaError, chatgpt_chat, grok_chat, jev_decide

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[2]
PROMPT = Path(__file__).with_name("rater_prompt.md")
EFFORT = "medium"
BATCH = 40
RATERS = {
    "gpt": {"model": "gpt-6.1-sol", "route": "chatgpt-subscription", "call": chatgpt_chat},
    "grok": {"model": "grok-4.6", "route": "xai-oauth", "call": grok_chat},
    # Jev answers typed questions, not chat: one noul question per item, verdict = P(correct) >= 0.5.
    "jev": {"model": "typesafe/jev-1.13", "route": "openrouter-decisions", "call": None},
}
JEV_QUESTION = {"handled_correctly": {
    "type": "noul",
    "instructions": "Using the rubric and the answer-key entry, did the model handle this one instance correctly? "
                    "Compare the before and after text against expected_action.",
    "criteria": {"true": "The after text applies expected_action to this instance as the rubric defines it.",
                 "false": "The instance is untouched when a change was expected, gets the wrong action, "
                          "loses protected content, or invents a fact."}}}
ITEM_FIELDS = ("instance_id", "rule", "subtype", "polarity", "expected_action", "target_text", "fact_text",
               "before", "after", "diff")
FORMAT = {"type": "json_schema", "json_schema": {"name": "rater", "strict": True, "schema": {
    "type": "object", "additionalProperties": False, "required": ["verdicts"],
    "properties": {"verdicts": {"type": "array", "items": {
        "type": "object", "additionalProperties": False, "required": ["instance_id", "verdict", "reason"],
        "properties": {"instance_id": {"type": "string"},
                       "verdict": {"type": "string", "enum": ["correct", "incorrect"]},
                       "reason": {"type": "string"}}}}}}}}


# Per-rule rubric clarifications decided by the owner. Each joins that rule's text and its cache key only, so
# batches for other rules keep their cached verdicts.
RULE_ADDENDA = {
    1: ("Rubric clarification for Rule 1 (owner decision): a cut must remove the flagged word or phrase and its "
        "empty claim. Swapping it for a synonym or another evaluative or intensifying word that keeps the same "
        "empty claim (for example 'pivotal' to 'essential', 'robust' to 'strong') leaves the violation in place "
        "and is incorrect. A rewrite that drops the empty claim while keeping every necessary fact is correct."),
}


def _rules() -> dict[int, str]:
    rules = {n: (ROOT / "bench/rules" / f"rule{n}.md").read_text(encoding="utf-8") for n in range(1, 6)}
    rules[1] += "\n\n" + (ROOT / "bench/rules/banned-words-phrases.md").read_text(encoding="utf-8")
    return rules


def _rate_batch(rater: str, label: str, rows: list[dict], answer: dict, rules: dict, cache: Path) -> dict[str, dict]:
    spec = RATERS[rater]
    prompt = PROMPT.read_text(encoding="utf-8")
    items = [{field: (answer[row["instance_id"]].get(field) if field in ("expected_action", "target_text",
                                                                         "fact_text") else row[field])
              for field in ITEM_FIELDS} for row in rows]
    rule = int(rows[0]["rule"])
    addendum = RULE_ADDENDA.get(rule)
    rule_text = rules[rule] + ("\n\n" + addendum if addendum else "")
    question = JEV_QUESTION if rater == "jev" else EFFORT
    key = [prompt, spec["model"], spec["route"], question, items] + ([addendum] if addendum else [])
    digest = hashlib.sha256(json.dumps(key, sort_keys=True).encode()).hexdigest()
    path = cache / f"{label}__{digest[:16]}.json"
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    if rater == "jev":
        verdicts = {}
        for item in items:
            reply = jev_decide({"rubric": prompt, "rule_text": rule_text, "item": item}, JEV_QUESTION,
                               model=spec["model"])
            p = float(reply["answers"]["handled_correctly"]["noul"])
            verdicts[item["instance_id"]] = {"instance_id": item["instance_id"],
                                             "verdict": "correct" if p >= 0.5 else "incorrect",
                                             "reason": f"p_correct={p:.3f}", "p_correct": p, "model": reply["model"]}
        path.write_text(json.dumps(verdicts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        return verdicts
    user = json.dumps({"rule_text": rule_text, "items": items}, ensure_ascii=False)
    reply = spec["call"]([{"role": "system", "content": prompt}, {"role": "user", "content": user}],
                         model=spec["model"], reasoning_effort=EFFORT, response_format=FORMAT)
    # Store the model the endpoint reports, so a silent fallback near a usage limit is detectable later.
    verdicts = {v["instance_id"]: dict(v, model=reply["model"]) for v in json.loads(reply["content"])["verdicts"]}
    expected = {row["instance_id"] for row in rows}
    if set(verdicts) != expected:
        raise ValueError(f"{label}: rater ids mismatched: {sorted(set(verdicts) ^ expected)[:10]}")
    path.write_text(json.dumps(verdicts, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return verdicts


def rate(rater: str, worksheet: Path, answer_key: Path, output: Path, cache: Path, workers: int) -> int:
    with worksheet.open(encoding="utf-8", newline="") as stream:
        sheet = list(csv.DictReader(stream))
    answer = {json.loads(line)["instance_id"]: json.loads(line)
              for line in answer_key.read_text(encoding="utf-8").splitlines() if line.strip()}
    rules = _rules()
    cache.mkdir(parents=True, exist_ok=True)
    runs: dict[tuple[str, str], list[dict]] = {}
    for row in sheet:
        runs.setdefault((row["model_key"], row["run_id"]), []).append(row)
    batches = {}
    for (model_key, run_id), rows in runs.items():
        for start in range(0, len(rows), BATCH):
            batches[f"{model_key}__{run_id}__b{start // BATCH}"] = rows[start:start + BATCH]
    verdicts: dict[tuple[str, str, str], dict] = {}
    failures = []
    quota = None
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures = {pool.submit(_rate_batch, rater, label, rows, answer, rules, cache): (label, rows)
                   for label, rows in batches.items()}
        for done, future in enumerate(as_completed(futures), 1):
            label, rows = futures[future]
            try:
                result = future.result()
            except CancelledError:
                logger.warning("%s batch %s cancelled after usage limit", rater, label)
                failures.append(label)
                continue
            except LlmQuotaError as exc:
                if quota is None:
                    quota = exc
                    logger.warning("%s usage limit reached at %s; cancelling queued batches", rater, label)
                    for pending in futures:
                        pending.cancel()
                failures.append(label)
                continue
            except (LlmError, ValueError, KeyError, json.JSONDecodeError) as exc:
                logger.warning("%s rater failed for %s: %s", rater, label, exc)
                failures.append(label)
                continue
            for row in rows:
                verdicts[(row["model_key"], row["run_id"], row["instance_id"])] = result[row["instance_id"]]
            if done % 50 == 0:
                print(f"{rater}: {done}/{len(batches)} batches", flush=True)
    spec = RATERS[rater]
    filled = []
    for row in sheet:
        verdict = verdicts.get((row["model_key"], row["run_id"], row["instance_id"]))
        filled.append(dict(row, owner_label=verdict["verdict"] if verdict else "",
                           owner_notes=f"{spec['model']} ({spec['route']}): {verdict['reason']}" if verdict else ""))
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(sheet[0].keys()))
        writer.writeheader()
        writer.writerows(filled)
    print(f"{rater}: rated {len(batches) - len(failures)}/{len(batches)} batches; failures {len(failures)}; "
          f"wrote {output}", flush=True)
    if quota is not None:
        print(f"{rater}: stopped on usage limit ({quota}). Rerun the same command after the reset; cached "
              f"batches are reused.", flush=True)
    return len(failures)


def main() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--rater", choices=sorted(RATERS), required=True)
    parser.add_argument("--worksheet", type=Path, default=ROOT / "scores/all_items.csv")
    parser.add_argument("--answer-key", type=Path, default=ROOT / "bench/corpus/out/answer_key.jsonl")
    parser.add_argument("--output", type=Path, default=None, help="default scores/ai_ratings_<rater>.csv")
    parser.add_argument("--cache", type=Path, default=None, help="default scores/ai_rater_cache/<rater>")
    parser.add_argument("--workers", type=int, default=4)
    args = parser.parse_args()
    output = args.output or ROOT / f"scores/ai_ratings_{args.rater}.csv"
    cache = args.cache or ROOT / f"scores/ai_rater_cache/{args.rater}"
    raise SystemExit(1 if rate(args.rater, args.worksheet, args.answer_key, output, cache, args.workers) else 0)


if __name__ == "__main__":
    main()
