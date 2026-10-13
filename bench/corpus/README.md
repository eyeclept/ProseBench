# Corpus pipeline

Run these commands from the repository root, in order. The inventory and injection use Grok 4.6. The audit uses paid OpenRouter calls. Set `OPENROUTER_API_KEY` before the audit.

1. Inventory the original essays: `.venv/bin/python -m bench.corpus.inventory`
2. Plant missing subtypes: `.venv/bin/python -m bench.corpus.inject`
3. Build the answer key: `.venv/bin/python -m bench.corpus.build_key`
4. Check the answer key: `.venv/bin/python -m bench.corpus.build_key --check`
5. Audit it: `.venv/bin/python -m bench.corpus.audit`

The commands write to `bench/corpus/out/`. Raw request logs exclude authorization headers. Review `out/audit_disagreements.md` by hand before scoring. The audit stops if its projected OpenRouter spend exceeds $0.50.

## Resume and rerun

- Inventory caches each rule in `out/P{n}/inventory_R{rule}.json`. A rerun skips cached rules. To redo one rule, delete its cache and raw log.
- Injection checkpoints each rule in `out/P{n}/inject_state.json`. A rerun resumes after the last finished rule. To redo a passage, delete that file and `injected.md`.
- Grok calls use `reasoning_effort` medium (low for repairs) and a strict JSON schema. A Grok call takes about 4-7 minutes. Running one process per passage in parallel works.

## Rule 4 auto-fill

Any non-ASCII character that the Rule 4 call and its repair leave uncovered gets a deterministic `other` instance with `expected_action` `ascii_equivalent`. Its note starts with `auto-filled`. These rows need owner review with the audit worksheet.
